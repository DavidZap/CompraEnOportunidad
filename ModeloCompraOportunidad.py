from pulp import *
import pandas as pd
from openpyxl import load_workbook, Workbook
import re
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder

st.title('Compra en Oportunidad')

data_file = st.file_uploader("Upload XLSX", type=["XLSX"])

if data_file is not None:
    df_input = pd.read_excel(r"Input.xlsx",sheet_name="Semanas")
    precio3=pd.read_excel(r"Input.xlsx",sheet_name="Precios")
    demanda3=pd.read_excel(r"Input.xlsx",sheet_name="Demanda")
    data=[df_input,precio3,demanda3]
    
    st.subheader('Demanda y Precios por Semana')
    st.write(data[0])
    
    # Creación de Conjuntos

    semanas= list(data[0]['Semanas'].unique())
    materiales = list(str(i) for i in data[0].Material.unique().tolist())
    
    # Parametros Precios
    
    precios2 = data[1].values.tolist()
    precios = makeDict([semanas, materiales],precios2,0)
    
    # Parametros Demanda
    
    demanda2 = data[2].values.tolist()
    demanda = makeDict([semanas, materiales],demanda2,0)
    
    
    # Definimos los valores por defecto de los parámetros
    
    inventarioInicial = 1140000 #kg
    inventarioMaximo = 25 # semanas #Buscar Equilibrio, para que no sea infactible 
    inventarioMinimo = 2 # semanas #Buscar Equilibrio, para que no sea infactible 
    costoKgInventario_INI = 5661 #$/kg
    CostoCapitalNM = 0.22 #tasa porcentaje 
    costoAlmacenamiento_valor = 270 # $/kg mes
    CostoTransporte_valor = 50 # $/kg 
    
    mod_co = LpProblem("Compra Oportunidad", LpMinimize)
    
    
    # Variables Obligatorias
    
    Compra = LpVariable.dicts("Compra",[(s,m) for s in semanas for m in materiales ],0, None)
    Inventario = LpVariable.dicts("Inventario",[(s,m) for s in semanas for m in materiales ],0, None) 
    CostoTotal = LpVariable.dicts("CostoTotal",[(s,m) for s in semanas for m in materiales ],0, None)
    
    # Función Objetivo

    mod_co += lpSum(CostoTotal[(s,m)] for s in semanas for m in materiales)
    
    # Restricciones Obligatorias
    
    # Cumplir la demanda
    
    for m in materiales:
        for s in semanas:
            mod_co += Inventario[(s,m)]  >= demanda[s][m]
            
    # Juego de Inventarios

    cont=-1
    for m in materiales:
        for s in semanas:
            if s == semanas[0]:
                mod_co += Inventario[(s,m)]  == inventarioInicial + Compra[(s,m)]  - demanda[s][m]
            else:
                mod_co += Inventario[(s,m)]  == Inventario[(semanas[cont],m)] + Compra[(s,m)]  - demanda[s][m] 
            cont=cont+1
        
    
    # Valores Positivos
    
    for s in semanas:
        mod_co += lpSum([Compra[(s,m)] for m in materiales ])  >= 0

    for s in semanas:
        mod_co += lpSum([Inventario[(s,m)] for m in materiales ])  >= 0


    def generar_interfaz_opciones_restriccion(restricciones):
        st.sidebar.title("Opciones de restricción")
        for restriccion in restricciones:
            restricciones[restriccion] = st.sidebar.checkbox(f"Incluir {restriccion}", value=True)
        return restricciones

    # Creamos un diccionario para almacenar las restricciones
    restricciones = {
        "Politica Inventario Máximo y Mínimo": True,
        "Costo de los Inventarios": True,
        "Costo de Transporte": True
    }
    
        
    # Creamos la interfaz de usuario con Streamlit, para encender o no restricciones 
    restricciones = generar_interfaz_opciones_restriccion(restricciones)


    inventarioInicial = st.slider("Inventario Inicial", 0, 2000000, 1140000)
    
    if restricciones["Politica Inventario Máximo y Mínimo"]:
        
        inventarioMaximo = st.slider("Inventario Máximo", 20, 25, 20)
        inventarioMinimo = st.slider("Inventario Minimo", 2, 4, 2)
        
        # Cumplir con politicas de Inventario

        for m in materiales:
            for s in semanas:
                mod_co += Inventario[(s,m)]  <= demanda[s][m]*inventarioMaximo

        for m in materiales:
            for s in semanas:
                mod_co += Inventario[(s,m)] >= demanda[s][m]*inventarioMinimo

        
        
    if restricciones["Costo de los Inventarios"]:
        
        costoKgInventario_INI = st.slider("Costo por Kg del Inventario", 0, 10000, 800)
        
        CostoInventario = LpVariable.dicts("CostoInventario",[(s,m) for s in semanas for m in materiales ],0, None)
        
        cont=-1
        for m in materiales:
            for s in semanas:
                if s == semanas[0]:
                    mod_co += CostoInventario[(s,m)]  ==(((inventarioInicial-demanda[s][m]) * costoKgInventario_INI) +(Compra[(s,m)]*precios[s][m])) 
                else:
                    mod_co += CostoInventario[(s,m)]  == (((Inventario[(semanas[cont],m)] -demanda[s][m]) * costoKgInventario_INI) +(Compra[(s,m)]*precios[s][m])) # /2
                cont=cont+1
            

        
    # if restricciones["Costo de Almacenamiento y Capital"]:
        
        costoAlmacenamiento_valor = st.slider("Costo Almacenamiento", 0, 1000, 270)
        
        CostoAlmacenamiento = LpVariable.dicts("CostoAlmacenamiento",[(s,m) for s in semanas for m in materiales ],0, None)
        
        # Costo de almacenamiento

        for m in materiales:
            for s in semanas:
                mod_co += CostoAlmacenamiento[(s,m)] == demanda[s][m]*inventarioMinimo* costoAlmacenamiento_valor
            
        
    # if restricciones["Costo de Capital"]:
        
        CostoCapitalNM = st.slider("Costo Capital", 0.0, 1.0, 0.22)
        
        CostoCapital = LpVariable.dicts("CostoCapital",[(s,m) for s in semanas for m in materiales ],0, None)
        
        # Costo de Capital

        for m in materiales:
            for s in semanas:
                mod_co += CostoCapital[(s,m)] == CostoInventario[(s,m)] * CostoCapitalNM

        
    if restricciones["Costo de Transporte"]:
        
        CostoTransporte_valor = st.slider("Costo Transporte", 0, 500, 50)
        
        CostoTransporte = LpVariable.dicts("CostoTransporte",[(s,m) for s in semanas for m in materiales ],0, None)
        

        for m in materiales:
            for s in semanas:
                mod_co += CostoTransporte[(s,m)] == demanda[s][m] * CostoTransporte_valor
        
        
#### Crear Funcion objetivo 

    if restricciones["Costo de los Inventarios"] == True & restricciones["Costo de Transporte"] == False :
        #CostoInventario[(s,m)] + CostoAlmacenamiento[(s,m)] + CostoCapital[(s,m)]

        for m in materiales:
            for s in semanas:
                mod_co += CostoTotal[(s,m)] ==  CostoInventario[(s,m)] + CostoAlmacenamiento[(s,m)] + CostoCapital[(s,m)]  + Compra[(s,m)]*precios[s][m]
                
    elif restricciones["Costo de Transporte"]== True & restricciones["Costo de los Inventarios"]  == False: 
        for m in materiales:
            for s in semanas:
                mod_co += CostoTotal[(s,m)] == CostoTransporte[(s,m)] + Compra[(s,m)]*precios[s][m]
                
    elif restricciones["Costo de Transporte"] == True & restricciones["Costo de los Inventarios"] ==True : 
        for m in materiales:
            for s in semanas:
                mod_co += CostoTotal[(s,m)] == CostoInventario[(s,m)] + CostoAlmacenamiento[(s,m)] + CostoCapital[(s,m)] + CostoTransporte[(s,m)] + Compra[(s,m)]*precios[s][m]
    else:
        for m in materiales:
            for s in semanas:
                mod_co += CostoTotal[(s,m)] == Compra[(s,m)]*precios[s][m] 
            
                
    
    # SOLVE

    mod_co.solve(solver = pulp.PULP_CBC_CMD(msg=True, threads=8, warmStart=True, timeLimit=260000, cuts=True, strong=True, presolve=True, gapRel=0.01))
    
    # Estatus Solución
    
    status = LpStatus[mod_co.status]
    st.write("Status:", status)
    st.write("Costo Total = ", "${:,.0f}".format(value(mod_co.objective)),  size=36)
    
    Resultados2 = []
    i=0
    for v in mod_co.variables():
        variable = re.findall(r"(\w+)_",v.name)[0]
        semana = re.findall(r"(\w+)',",v.name)[0]
        codigo= re.findall(r"s*'(\d+)'",v.name)[0]
        demanda = demanda2[i][0]
        precios = precios2[i][0]
        i+=1
        if i == len(demanda2):
            i=0
        Resultados2.append({"Variable": variable, "Semana": semana, "Codigo": codigo, "Valor":v.varValue, "Demanda":demanda,"Precios":precios})
    
    Resultado = pd.DataFrame(Resultados2)
        
    df_pivot = Resultado.pivot(index=['Semana', 'Codigo'], columns='Variable', values='Valor').reset_index()
    for i in list(df_pivot.columns)[2:]:
        df_pivot[i] = df_pivot[i].apply(lambda x: int('{:.0f}'.format(x)))
    
    st.subheader('Resultados de la Optimización')
    st.write(df_pivot)
    
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')
    
    csv = convert_df(df_pivot)
    
    st.download_button(
   "Press to Download",
   csv,
   "file.csv",
   "text/csv",
   key='download-csv')
    
    # Creación del Grafico 
    
    
    
    Resultado_Compras = Resultado[Resultado['Variable']=="Compra"]
    Resultado_Inventario = Resultado[Resultado['Variable']=="Inventario"]
    Resultado_CostoTotal = Resultado[Resultado['Variable']=="CostoTotal"]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(x=Resultado_Compras['Semana'], y=Resultado_Compras['Valor'], name='Compras'))

    fig.add_trace(go.Scatter(x=Resultado_Inventario['Semana'], y=Resultado_Inventario['Valor'], 
                             name='Inventario', mode='lines', line=dict(color='red'), legendrank=True))
    
    fig.add_trace(go.Scatter(x=Resultado_Compras['Semana'], y=Resultado_Compras['Demanda'], 
                             name='Demanda', mode='lines', line=dict(color='green'), legendrank=True))

    fig.add_trace(go.Scatter(x=Resultado_Compras['Semana'], y=Resultado_Compras['Precios'], 
                             name='Precios', mode='lines', line=dict(color='orange'), legendrank=True), secondary_y=True)
    
    fig.add_trace(go.Scatter(x=Resultado_CostoTotal['Semana'], y=Resultado_CostoTotal['Valor'], 
                             name='Costo Total', mode='markers', line=dict(color='purple'), legendrank=True), secondary_y=True)
    
    if restricciones["Costo de los Inventarios"] :
        
        Resultado_CostoAlmacenamiento = Resultado[Resultado['Variable']=="CostoAlmacenamiento"]
        Resultado_CostoInventario = Resultado[Resultado['Variable']=="CostoInventario"]
        Resultado_CostoCapital = Resultado[Resultado['Variable']=="CostoCapital"]
        
        fig.add_trace(go.Scatter(x=Resultado_CostoAlmacenamiento['Semana'], y=Resultado_CostoAlmacenamiento['Valor'], 
                                 name='Costo Almacenamiento', mode='lines', line=dict(color='grey'), legendrank=True), secondary_y=True)

        fig.add_trace(go.Scatter(x=Resultado_CostoInventario['Semana'], y=Resultado_CostoInventario['Valor'], 
                                 name='Costo Inventario', mode='markers', line=dict(color='pink'), legendrank=True), secondary_y=True)

        fig.add_trace(go.Scatter(x=Resultado_CostoCapital['Semana'], y=Resultado_CostoCapital['Valor'], 
                                 name='Costo Capital', mode='markers', line=dict(color='brown'), legendrank=True), secondary_y=True)
    
    if restricciones["Costo de Transporte"]:

        Resultado_CostoTransporte = Resultado[Resultado['Variable']=="CostoTransporte"]


        fig.add_trace(go.Scatter(x=Resultado_CostoTransporte['Semana'], y=Resultado_CostoTransporte['Valor'], 
                                 name='Costo Transporte', mode='markers', line=dict(color='gold'), legendrank=True), secondary_y=True)



    fig.update_layout(title='Compra de Oportunidad',
                      xaxis=dict(title='Semana'),
                      yaxis=dict(title='Unidades'),
                      yaxis2=dict(title='Precios', overlaying='y', side='right'))

    st.write(fig)


  
        
    
    

import streamlit as st

def calcular_costos(ventas, costo_materiales, costo_labor, costo_capital, costo_transporte, restricciones):
    # Calcula el costo total de producción en función de las entradas y restricciones
    if restricciones["capital"] == True:
        costo_produccion = ventas * (costo_materiales + costo_labor + costo_capital + costo_transporte)
    else:
        costo_produccion = ventas * (costo_materiales + costo_labor + costo_transporte)

    if restricciones["transporte"] == True:
        costo_produccion += costo_transporte

    return costo_produccion

# Definimos los valores por defecto de los parámetros
ventas = 100
costo_materiales = 10
costo_labor = 5
costo_capital = 2
costo_transporte = 1

# Creamos un diccionario para almacenar las restricciones
restricciones = {
    "capital": True,
    "transporte": True
}

# Creamos la interfaz de usuario con Streamlit
st.sidebar.title("Opciones de restricción")
restricciones["capital"] = st.sidebar.checkbox("Incluir costo de capital")
restricciones["transporte"] = st.sidebar.checkbox("Incluir costo de transporte")

ventas = st.slider("Ventas", 0, 1000, 100)
costo_materiales = st.slider("Costo de materiales", 0, 100, 10)
costo_labor = st.slider("Costo de labor", 0, 50, 5)
costo_capital = st.slider("Costo de capital", 0, 10, 2)
costo_transporte = st.slider("Costo de transporte", 0, 10, 1)

costo_produccion = calcular_costos(ventas, costo_materiales, costo_labor, costo_capital, costo_transporte, restricciones)

st.write("El costo total de producción es:", costo_produccion)

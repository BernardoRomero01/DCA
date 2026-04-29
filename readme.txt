Aplicación de streamlit sencilla para realizar Decline Curve Analysis y exportar los resultados a un Excel.

Primero se debe seleccionar el archivo Excel en el que están los datos. Tiene que haber una primera columna de fecha en formato dd/mm/yyyy, las siguientes columnas pueden ser cualquier dato, pero se espera que sea producción de un pozo. Se adjunta un archivo Excel de ejemplo.

Una vez que se cargue el archivo se generará la pantalla principal.

En las opciones de la derecha se puede seleccionar, de arriba hacia abajo:

- En base a las columnas que tiene el Excel, establecer a qué curva se le quiere hacer el DCA.

- En base a las columnas que tiene el Excel, cuales curvas se ven en el gráfico (aunque solo se utilizará la seleccionada previamente para hacer DCA).

- El rango de valores que se quieren utilizar para hacer el DCA, ya que tal vez no se quieran utilizar los primeros valores o algunos de los últimos para realizar la estimación.

- Los días hacia adelante en los que se quiere realizar el pronóstico de declino, por defecto es 1 año.

La imagen se puede agrandar, hacer zoom o copiar y pegar si se quiere en tu computadora.

Por encima del gráfico se obtiene: el Qi, Di y b de la fórmula de DCA Q=Qi/(1+b*Di*t)^(1/b) y el declino anual, que se obtiene entre el último control (Q1) y el valor de producción un año después(Q2): Declino anual= (Q1-Q2)/Q1*100

Debajo del gráfico está la opción de descargar la curva de declino obtenida.


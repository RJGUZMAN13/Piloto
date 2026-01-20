import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt
import os

# --- Inicialización de base de datos temporal ---
if "orders" not in st.session_state:
    st.session_state.orders = pd.DataFrame(columns=[
        "ID", "Fecha", "Supervisor", "Área", "Materiales", "Actividades", "Requerimientos", "Estatus"
    ])

# --- Encabezado ---
st.title("📋 Sistema de Órdenes de Trabajo")
st.write("Prototipo interactivo con Streamlit")

# --- Formulario para nueva orden ---
st.header("➕ Crear nueva orden")
with st.form("new_order_form"):
    supervisor = st.text_input("Supervisor")
    area = st.selectbox("Área", ["Gats", "Ford", "EPU4"])
    materiales = st.text_area("Materiales requeridos")
    actividades = st.text_area("Actividades")
    requerimientos = st.text_area("Requerimientos adicionales")
    submitted = st.form_submit_button("Enviar orden")

    if submitted:
        new_order = {
            "ID": len(st.session_state.orders) + 1,
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Supervisor": supervisor,
            "Área": area,
            "Materiales": materiales,
            "Actividades": actividades,
            "Requerimientos": requerimientos,
            "Estatus": "Por hacer"
        }
        st.session_state.orders = pd.concat([st.session_state.orders, pd.DataFrame([new_order])], ignore_index=True)
        st.success("✅ Orden registrada correctamente")

# --- Visualización de órdenes ---
st.header("📊 Órdenes registradas")
if not st.session_state.orders.empty:
    st.dataframe(st.session_state.orders, use_container_width=True)

    # --- Actualizar estatus ---
    st.subheader("🔄 Actualizar estatus")
    order_id = st.number_input("ID de la orden", min_value=1, max_value=len(st.session_state.orders), step=1)
    new_status = st.selectbox("Nuevo estatus", ["Por hacer", "En progreso", "Hecho"])
    if st.button("Actualizar estatus"):
        st.session_state.orders.loc[st.session_state.orders["ID"] == order_id, "Estatus"] = new_status
        st.success(f"Orden {order_id} actualizada a '{new_status}'")

    # --- Eliminar orden ---
    st.subheader("🗑️ Eliminar orden")
    delete_id = st.number_input("ID de la orden a eliminar", min_value=1, max_value=len(st.session_state.orders), step=1, key="delete_id")
    if st.button("Eliminar orden"):
        st.session_state.orders = st.session_state.orders[st.session_state.orders["ID"] != delete_id].reset_index(drop=True)
        st.success(f"Orden {delete_id} eliminada correctamente")
        st.session_state.orders["ID"] = range(1, len(st.session_state.orders) + 1)

# --- Reporte detallado ---
st.header("📈 Reporte detallado")
if not st.session_state.orders.empty:
    status_counts = st.session_state.orders["Estatus"].value_counts()
    area_counts = st.session_state.orders["Área"].value_counts()

    st.subheader("Órdenes por estatus")
    st.bar_chart(status_counts)

    st.subheader("Órdenes por área")
    st.bar_chart(area_counts)

    # --- Exportar a Excel ---
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        st.session_state.orders.to_excel(writer, index=False, sheet_name="Órdenes")
        pd.DataFrame(status_counts).to_excel(writer, sheet_name="ResumenEstatus")
        pd.DataFrame(area_counts).to_excel(writer, sheet_name="ResumenÁreas")
    st.download_button(
        label="⬇️ Descargar reporte en Excel",
        data=excel_buffer.getvalue(),
        file_name="reporte_ordenes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Exportar a PDF con gráficos embebidos ---
    fig1, ax1 = plt.subplots()
    status_counts.plot(kind='bar', ax=ax1)
    ax1.set_title("Órdenes por Estatus")
    ax1.set_ylabel("Cantidad")
    fig1.tight_layout()
    img1_path = "grafico_estatus.png"
    fig1.savefig(img1_path)

    fig2, ax2 = plt.subplots()
    area_counts.plot(kind='bar', ax=ax2)
    ax2.set_title("Órdenes por Área")
    ax2.set_ylabel("Cantidad")
    fig2.tight_layout()
    img2_path = "grafico_area.png"
    fig2.savefig(img2_path)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Reporte de Órdenes de Trabajo", ln=True, align="C")
    pdf.cell(200, 10, txt=f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)

    for i, row in st.session_state.orders.iterrows():
        pdf.multi_cell(0, 10, txt=f"ID: {row['ID']} | Supervisor: {row['Supervisor']} | Área: {row['Área']} | "
                                  f"Estatus: {row['Estatus']} | Materiales: {row['Materiales']} | "
                                  f"Actividades: {row['Actividades']} | Requerimientos: {row['Requerimientos']}", border=0)
        pdf.ln(2)

    pdf.image(img1_path, x=10, y=pdf.get_y(), w=180)
    pdf.ln(65)
    pdf.image(img2_path, x=10, y=pdf.get_y(), w=180)

    pdf_buffer = BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin1')
    pdf_buffer.write(pdf_output)
    pdf_buffer.seek(0)

    st.download_button(
        label="⬇️ Descargar reporte en PDF",
        data=pdf_buffer,
        file_name="reporte_ordenes.pdf",
        mime="application/pdf"
    )

    os.remove(img1_path)
    os.remove(img2_path)
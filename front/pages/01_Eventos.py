from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

import api_client as api
import ui
from api_client import ApiError

ui.preparar_pagina()

st.title("Eventos")
ui.mostrar_flash()

salones_lista = ui.cargar(api.get_salones)
servicios_lista = ui.cargar(api.get_servicios)
clientes_lista = ui.cargar(api.get_clientes)
staff_lista = ui.cargar(api.get_staff)

salones = ui.mapa(salones_lista, "nombre_salon")
servicios = {s["id"]: s for s in servicios_lista}
clientes = ui.mapa(clientes_lista, "nombre")
staff = {s["id"]: s for s in staff_lista}


def selector_fecha_hora(etiqueta: str, valor: datetime, clave: str) -> datetime:
    c1, c2 = st.columns(2)
    d = c1.date_input(f"{etiqueta} · fecha", value=valor.date(), key=f"{clave}_d", format="DD/MM/YYYY")
    h = c2.time_input(f"{etiqueta} · hora", value=valor.time(), key=f"{clave}_h", step=timedelta(minutes=30))
    return datetime.combine(d, h)


tab_lista, tab_crear, tab_gestion = st.tabs(["Listado", "Crear evento", "Gestionar un evento"])

# Listado
with tab_lista:
    f1, f2, f3 = st.columns(3)
    estado = f1.selectbox("Estado", ["Todos"] + ui.ESTADOS)
    cliente_f = f2.selectbox("Cliente", [None] + list(clientes), format_func=lambda i: "Todos" if i is None else clientes[i])
    salon_f = f3.selectbox("Salón", [None] + list(salones), format_func=lambda i: "Todos" if i is None else salones[i])

    eventos = ui.cargar(api.get_eventos, None if estado == "Todos" else estado, cliente_f, salon_f)
    if eventos:
        df = pd.DataFrame(eventos).sort_values("inicio")
        st.dataframe(
            pd.DataFrame({
                "ID": df["id"],
                "Evento": df["nombre"],
                "Tipo": df["tipo"],
                "Estado": df["estado"],
                "Inicio": df["inicio"].map(ui.fecha_hora),
                "Fin": df["fin"].map(ui.fecha_hora),
                "Salón": df["salon_id"].map(salones),
                "Cliente": df["cliente_id"].map(clientes),
                "Aforo": df["aforo_esperado"],
                "Valor total": df["valor_total_cotizado"].map(ui.dinero),
                "Tasa asistencia": df["tasa_asistencia"].map(ui.porcentaje),
            }),
            hide_index=True,
            width="stretch",
        )
        st.caption(f"{len(df)} evento(s)")
    else:
        st.info("No hay eventos con esos filtros.")

# Crear evento
with tab_crear:
    st.markdown("**Paso 1.** Indique el horario y el aforo. Se consultan los salones libres con la función `fn_salones_disponibles` (A5).")
    manana = datetime.combine(date.today() + timedelta(days=7), time(8, 0))
    inicio = selector_fecha_hora("Inicio", manana, "nuevo_inicio")
    fin = selector_fecha_hora("Fin", manana + timedelta(hours=4), "nuevo_fin")
    aforo = st.number_input("Aforo esperado (personas)", min_value=1, value=50, step=10, key="nuevo_aforo")

    if st.button("Buscar salones disponibles", type="primary"):
        try:
            st.session_state["disp_crear"] = {
                "clave": (inicio, fin, aforo),
                "salones": api.get_salones_disponibles(inicio, fin, aforo),
            }
        except ApiError as e:
            st.session_state.pop("disp_crear", None)
            ui.mostrar_error(e)

    busqueda = st.session_state.get("disp_crear")
    if busqueda and busqueda["clave"] != (inicio, fin, aforo):
        st.info("Cambió el horario o el aforo: vuelva a buscar salones disponibles.")
    elif busqueda:
        libres = busqueda["salones"]
        if not libres:
            st.warning("No hay salones disponibles para ese horario y aforo. Pruebe con otro horario.")
        else:
            st.markdown(f"**Paso 2.** {len(libres)} salón(es) disponible(s). Complete los datos del evento.")
            with st.form("form_crear_evento"):
                salon_id = st.radio(
                    "Salón (solo se muestran los disponibles)",
                    [s["salon_id"] for s in libres],
                    format_func=lambda i: next(
                        f"{s['nombre_salon']} · {s['tamano']} · cap. {s['capacidad']} · costo salón {ui.dinero(s['costo_estimado'])}"
                        for s in libres if s["salon_id"] == i
                    ),
                )
                nombre = st.text_input("Nombre del evento", max_chars=100)
                c1, c2 = st.columns(2)
                tipo = c1.selectbox("Tipo", ui.TIPOS_EVENTO)
                cliente_id = c2.selectbox("Cliente", list(clientes), format_func=lambda i: clientes[i])
                coordinadores = sorted(staff.values(), key=lambda s: (s["cargo"] != "Coordinador", s["nombre"]))
                coordinador_id = st.selectbox(
                    "Coordinador (staff)",
                    [s["id"] for s in coordinadores],
                    format_func=lambda i: f"{staff[i]['nombre']} — {staff[i]['cargo']} de {staff[i]['area']}",
                )
                if st.form_submit_button("Crear evento", type="primary"):
                    payload = {
                        "nombre": nombre.strip(), "tipo": tipo,
                        "inicio": inicio.isoformat(), "fin": fin.isoformat(),
                        "aforo_esperado": int(aforo), "salon_id": salon_id,
                        "cliente_id": cliente_id, "coordinador_id": coordinador_id,
                    }
                    try:
                        nuevo = api.crear_evento(payload)
                        st.session_state.pop("disp_crear", None)
                        st.session_state["evento_sel"] = nuevo["id"]
                        ui.exito(
                            f"Evento #{nuevo['id']} «{nuevo['nombre']}» creado como **{nuevo['estado']}**. "
                            f"Valor calculado por el trigger A3: **{ui.dinero(nuevo['valor_total_cotizado'])}**. "
                            "Configure sus servicios en la pestaña «Gestionar un evento»."
                        )
                    except ApiError as e:
                        ui.mostrar_error(e)

# Gestionar un evento
with tab_gestion:
    todos = ui.cargar(api.get_eventos)
    if not todos:
        st.stop()
    todos = sorted(todos, key=lambda e: e["id"], reverse=True)
    ids = [e["id"] for e in todos]
    por_id = {e["id"]: e for e in todos}
    if st.session_state.get("evento_sel") not in ids:
        st.session_state["evento_sel"] = ids[0]
    evento_id = st.selectbox("Evento", ids, key="evento_sel", format_func=lambda i: ui.etiqueta_evento(por_id[i]))

    try:
        ev = api.get_evento(evento_id)
    except ApiError as e:
        ui.mostrar_error(e)
        st.stop()

    st.subheader(f"{ev['estado']} · {salones.get(ev['salon_id'], ev['salon_id'])}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Aforo / inscritos", f"{ev['aforo_esperado']} / {ev['asistencia']['inscritos']}")
    m2.metric("Valor total", ui.dinero(ev["valor_total_cotizado"]))
    m3.metric("Tasa asistencia", ui.porcentaje(ev["tasa_asistencia"]))
    st.caption(
        f"{ui.fecha_hora(ev['inicio'])} → {ui.fecha_hora(ev['fin'])} · Cliente: {clientes.get(ev['cliente_id'])} · "
        f"Coordinador: {staff.get(ev['coordinador_id'], {}).get('nombre', '—')} · "
        f"Llegaron: {ev['asistencia']['asistentes_reales']}"
    )

    t_cot, t_serv, t_estado, t_repro, t_aud = st.tabs(
        ["Cotización", "Servicios", "Estado", "Reprogramar", "Auditoría"]
    )

    # Cotización
    with t_cot:
        cot = ui.cargar(api.get_cotizacion, evento_id, defecto={})
        if cot:
            filas = [{
                "Concepto": f"Alquiler {salones.get(ev['salon_id'])}",
                "Cobro": "Hora",
                "Cantidad": cot["hora_salon"],
                "Precio unitario": ui.dinero(cot["precio_hora_salon"]),
                "Subtotal": ui.dinero(cot["valor_total_salon"]),
            }] + [{
                "Concepto": s["nombre_servicio"],
                "Cobro": s["unidad_cobro"],
                "Cantidad": s["cantidad"],
                "Precio unitario": ui.dinero(s["precio_unidad_cotizado"]),
                "Subtotal": ui.dinero(s["valor_total_cotizado"]),
            } for s in cot["servicios"]]
            st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")

            c1, c2, c3 = st.columns(3)
            c1.metric("Salón", ui.dinero(cot["valor_total_salon"]))
            c2.metric("Servicios", ui.dinero(cot["total_servicios"]))
            c3.metric("Total (guardado por el trigger A3)", ui.dinero(cot["valor_total_cotizado"]))
            suma = float(cot["valor_total_salon"]) + float(cot["total_servicios"])
            if abs(suma - float(cot["valor_total_cotizado"])) < 0.5:
                st.success("Salón + servicios = total (el valor guardado en la base coincide con el desglose)")
            else:
                st.warning(f"El desglose suma {ui.dinero(suma)} y el total guardado es {ui.dinero(cot['valor_total_cotizado'])}.")
            st.caption("Los precios unitarios están congelados al momento de contratar: si cambia el catálogo, esta cotización no cambia.")

    # Servicios
    with t_serv:
        contratados = ev["servicios"]
        if contratados:
            tabla_serv = pd.DataFrame([{
                "Servicio": servicios.get(s["servicio_id"], {}).get("nombre_servicio", s["servicio_id"]),
                "Cobro": servicios.get(s["servicio_id"], {}).get("unidad_cobro", ""),
                "Cantidad": s["cantidad"],
                "Precio congelado": ui.dinero(s["precio_unidad_cotizado"]),
                "Precio catálogo hoy": ui.dinero(servicios.get(s["servicio_id"], {}).get("precio")),
            } for s in contratados])
            st.dataframe(tabla_serv, hide_index=True, width="stretch")
        else:
            st.info("Este evento aún no tiene servicios contratados.")

        if ev["estado"] in ("Finalizado", "Cancelado"):
            st.caption(f"El evento está {ev['estado']}: el trigger A3 rechazará cualquier cambio en sus servicios.")

        c_add, c_mod = st.columns(2)
        with c_add:
            st.markdown("**Agregar servicio**")
            with st.form("form_add_serv"):
                sid = st.selectbox(
                    "Servicio", list(servicios),
                    format_func=lambda i: f"{servicios[i]['nombre_servicio']} ({servicios[i]['unidad_cobro']}, {ui.dinero(servicios[i]['precio'])})",
                )
                automatica = st.checkbox(
                    "Cantidad automática", value=True,
                    help="Por persona → aforo esperado; por hora → duración del evento redondeada hacia arriba (lo calcula el trigger A3).",
                )
                cantidad = st.number_input("Cantidad (si no es automática)", min_value=1, value=1)
                if st.form_submit_button("Agregar", type="primary"):
                    try:
                        api.agregar_servicio_evento(evento_id, sid, None if automatica else int(cantidad))
                        ui.exito(f"Servicio «{servicios[sid]['nombre_servicio']}» agregado. El total del evento se recalculó en la base.")
                    except ApiError as e:
                        ui.mostrar_error(e)

        with c_mod:
            st.markdown("**Modificar o quitar un servicio contratado**")
            if contratados:
                with st.form("form_mod_serv"):
                    sid_mod = st.selectbox(
                        "Servicio contratado", [s["servicio_id"] for s in contratados],
                        format_func=lambda i: servicios.get(i, {}).get("nombre_servicio", i),
                    )
                    nueva_cant = st.number_input("Nueva cantidad", min_value=1, value=1)
                    b1, b2 = st.columns(2)
                    modificar = b1.form_submit_button("Modificar cantidad")
                    quitar = b2.form_submit_button("Quitar servicio")
                    try:
                        if modificar:
                            api.actualizar_servicio_evento(evento_id, sid_mod, int(nueva_cant))
                            ui.exito("Cantidad actualizada y total recalculado.")
                        if quitar:
                            api.quitar_servicio_evento(evento_id, sid_mod)
                            ui.exito("Servicio quitado y total recalculado.")
                    except ApiError as e:
                        ui.mostrar_error(e)
            else:
                st.caption("No hay servicios para modificar.")

    # Estado
    with t_estado:
        st.markdown(
            "Flujo permitido: **Cotizado → Confirmado → Finalizado**, y **Cancelado** desde Cotizado o Confirmado. "
            "Finalizado y Cancelado son definitivos. Solo se puede finalizar cuando ya pasó la hora de fin "
            "(al hacerlo, el trigger A4 calcula la tasa de asistencia)."
        )
        b1, b2, b3 = st.columns(3)
        nuevo_estado = None
        if b1.button("Confirmar", width="stretch"):
            nuevo_estado = "Confirmado"
        if b2.button("Finalizar", width="stretch"):
            nuevo_estado = "Finalizado"
        if b3.button("Cancelar evento", width="stretch"):
            nuevo_estado = "Cancelado"
        if nuevo_estado:
            try:
                r = api.cambiar_estado_evento(evento_id, nuevo_estado)
                extra = f" Tasa de asistencia: **{ui.porcentaje(r['tasa_asistencia'])}**." if nuevo_estado == "Finalizado" else ""
                ui.exito(f"Evento #{evento_id} ahora está **{r['estado']}**.{extra}")
            except ApiError as e:
                ui.mostrar_error(e)

    # Reprogramar
    with t_repro:
        st.markdown("Cambie salón, horario o aforo. El trigger A1 valida capacidad, salón habilitado y cruces (con 1 h de montaje).")
        ini_actual = datetime.fromisoformat(ev["inicio"])
        fin_actual = datetime.fromisoformat(ev["fin"])
        n_ini = selector_fecha_hora("Nuevo inicio", ini_actual, f"rep_ini_{evento_id}")
        n_fin = selector_fecha_hora("Nuevo fin", fin_actual, f"rep_fin_{evento_id}")
        c1, c2 = st.columns(2)
        n_aforo = c1.number_input("Aforo esperado", min_value=1, value=int(ev["aforo_esperado"]), key=f"rep_af_{evento_id}")
        n_salon = c2.selectbox(
            "Salón", list(salones), index=list(salones).index(ev["salon_id"]), key=f"rep_sal_{evento_id}",
            format_func=lambda i: next(f"{s['nombre_salon']} (cap. {s['capacidad']}{'' if s['habilitado'] else ', deshabilitado'})"
                                       for s in salones_lista if s["id"] == i),
        )
        cambios = {}
        if n_ini != ini_actual:
            cambios["inicio"] = n_ini.isoformat()
        if n_fin != fin_actual:
            cambios["fin"] = n_fin.isoformat()
        if n_aforo != ev["aforo_esperado"]:
            cambios["aforo_esperado"] = int(n_aforo)
        if n_salon != ev["salon_id"]:
            cambios["salon_id"] = n_salon

        if cambios:
            st.caption("Cambios a enviar: " + ", ".join(cambios))
        if st.button("Guardar reprogramación", type="primary", disabled=not cambios):
            try:
                r = api.reprogramar_evento(evento_id, cambios)
                ui.exito(f"Evento reprogramado. Nuevo valor total: **{ui.dinero(r['valor_total_cotizado'])}**. El cambio quedó en la auditoría.")
            except ApiError as e:
                ui.mostrar_error(e)

    # Auditoría
    with t_aud:
        auditoria = ui.cargar(api.get_auditoria, evento_id)
        if auditoria:
            nombres_salon = {str(k): v for k, v in salones.items()}
            st.dataframe(pd.DataFrame([{
                "Fecha": ui.fecha_hora(a["fecha_hora"]),
                "Usuario": a["usuario"],
                "Campo": a["campo_modificado"],
                "Antes": nombres_salon.get(a["valor_anterior"], a["valor_anterior"]) if a["campo_modificado"] == "salon_id" else a["valor_anterior"],
                "Después": nombres_salon.get(a["valor_nuevo"], a["valor_nuevo"]) if a["campo_modificado"] == "salon_id" else a["valor_nuevo"],
            } for a in auditoria]), hide_index=True, width="stretch")
        else:
            st.info("Este evento no tiene cambios registrados.")

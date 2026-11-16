window.PEDIDOS = {
  "etiqueta": "Maqueta · datos sintéticos",
  "fecha_referencia": "2026-11-14",
  "fuente": "sintetico_demo",
  "extracto_completo": true,
  "pacientes_revisados": 4,
  "pacientes_extracto": 4,
  "pedidos": [
    {
      "id": "S3-1-2026-11-02",
      "regla": "S3",
      "grupo": 1,
      "prioridad": 8.543005670481474,
      "prueba": "FGe",
      "motivo": "FGe 78 → 61 (2024-11-05 a 2026-11-02, 3 valores): -8.5 ml/min/1,73 m²/año",
      "pedido": "Función renal en descenso: repetir FGe + CAC, valorar",
      "nota": "Descenso de FGe (KDIGO 2012, rec. 2.1.3): se solicita FGe y CAC.",
      "fecha_origen": "2026-11-02",
      "grupo_nombre": "Empeorando",
      "person_id": 1,
      "nombre": "Manuel",
      "edad": 72,
      "sexo": "Hombre",
      "sip": null,
      "diagnosticos": [
        "Hipertensión"
      ],
      "hoy_en_consulta": false,
      "hora_cita": null,
      "aviso_farmaco": null,
      "fecha_revision": "2026-12-14",
      "tambien": [],
      "anotaciones": [],
      "fuentes": [
        {
          "tabla": "condition_occurrence",
          "dato": "I10 · sin N18 (ERC sin codificar)"
        },
        {
          "tabla": "measurement",
          "dato": "CAC 12 mg/g (2026-11-02) · FGe 61 (2026-11-02) · FGe 69 (2025-11-10) · FGe 78 (2024-11-05)"
        },
        {
          "tabla": "drug_exposure",
          "dato": "sin dispensaciones registradas"
        },
        {
          "tabla": "pedido_pendiente",
          "dato": "ningún pedido vigente"
        },
        {
          "tabla": "note",
          "dato": "ninguna nota con una cita comprobada"
        }
      ],
      "evolutivos": [],
      "procedencia": [
        {
          "prueba": "CAC",
          "fecha": "2026-11-02",
          "valor": 12.0,
          "unidad": "mg/g"
        },
        {
          "prueba": "FGe",
          "fecha": "2026-11-02",
          "valor": 61.0,
          "unidad": "mL/min/1.73m2"
        },
        {
          "prueba": "FGe",
          "fecha": "2025-11-10",
          "valor": 69.0,
          "unidad": "mL/min/1.73m2"
        },
        {
          "prueba": "FGe",
          "fecha": "2024-11-05",
          "valor": 78.0,
          "unidad": "mL/min/1.73m2"
        }
      ]
    },
    {
      "id": "S1b-2-2026-02-12",
      "regla": "S1b",
      "grupo": 2,
      "prioridad": 0.0,
      "prueba": "CAC",
      "motivo": "CAC 85 mg/g (A2) el 2026-02-12, sin repetir en 9 meses y sin código de ERC",
      "pedido": "Albuminuria sin confirmar: repetir CAC en primera orina de la mañana",
      "nota": "CAC alterado sin confirmar (KDIGO 2024, PP 1.1.3.2 y 1.3.1.2): se solicita repetición en primera orina de la mañana (chorro medio); evitar durante la menstruación, tras ejercicio intenso o con infección urinaria sintomática o hematuria (tabla 16).",
      "fecha_origen": "2026-02-12",
      "grupo_nombre": "Sin seguimiento",
      "person_id": 2,
      "nombre": "Pilar",
      "edad": 67,
      "sexo": "Mujer",
      "sip": null,
      "diagnosticos": [
        "Diabetes tipo 2"
      ],
      "hoy_en_consulta": true,
      "hora_cita": "10:40",
      "aviso_farmaco": null,
      "fecha_revision": "2026-12-14",
      "tambien": [],
      "anotaciones": [],
      "fuentes": [
        {
          "tabla": "condition_occurrence",
          "dato": "E11.9 · sin N18 (ERC sin codificar)"
        },
        {
          "tabla": "measurement",
          "dato": "CAC 85 mg/g (2026-02-12) · FGe 74 (2026-02-12)"
        },
        {
          "tabla": "drug_exposure",
          "dato": "sin dispensaciones registradas"
        },
        {
          "tabla": "pedido_pendiente",
          "dato": "ningún pedido vigente"
        },
        {
          "tabla": "note",
          "dato": "ninguna nota con una cita comprobada"
        }
      ],
      "evolutivos": [],
      "procedencia": [
        {
          "prueba": "CAC",
          "fecha": "2026-02-12",
          "valor": 85.0,
          "unidad": "mg/g"
        },
        {
          "prueba": "FGe",
          "fecha": "2026-02-12",
          "valor": 74.0,
          "unidad": "mL/min/1.73m2"
        }
      ]
    },
    {
      "id": "S1a-3-2025-05-12",
      "regla": "S1a",
      "grupo": 3,
      "prioridad": 0.0,
      "prueba": "CAC",
      "motivo": "Último CAC el 2025-05-12 (18 meses)",
      "pedido": "Solicitar CAC",
      "nota": "Cribado anual de ERC (PROT-AP ERC 2025): se solicita CAC.",
      "fecha_origen": "2025-05-12",
      "grupo_nombre": "Prueba pendiente",
      "person_id": 3,
      "nombre": "Rosa",
      "edad": 59,
      "sexo": "Mujer",
      "sip": null,
      "diagnosticos": [
        "Diabetes tipo 2",
        "Hipertensión"
      ],
      "hoy_en_consulta": false,
      "hora_cita": null,
      "aviso_farmaco": null,
      "fecha_revision": "2026-12-14",
      "tambien": [],
      "anotaciones": [],
      "fuentes": [
        {
          "tabla": "condition_occurrence",
          "dato": "E11.9, I10 · sin N18 (ERC sin codificar)"
        },
        {
          "tabla": "measurement",
          "dato": "CAC 18 mg/g (2025-05-12) · FGe 88 (2026-06-01) · FGe 91 (2025-05-12)"
        },
        {
          "tabla": "drug_exposure",
          "dato": "sin dispensaciones registradas"
        },
        {
          "tabla": "pedido_pendiente",
          "dato": "ningún pedido vigente"
        },
        {
          "tabla": "note",
          "dato": "ninguna nota con una cita comprobada"
        }
      ],
      "evolutivos": [],
      "procedencia": [
        {
          "prueba": "FGe",
          "fecha": "2026-06-01",
          "valor": 88.0,
          "unidad": "mL/min/1.73m2"
        },
        {
          "prueba": "CAC",
          "fecha": "2025-05-12",
          "valor": 18.0,
          "unidad": "mg/g"
        },
        {
          "prueba": "FGe",
          "fecha": "2025-05-12",
          "valor": 91.0,
          "unidad": "mL/min/1.73m2"
        }
      ]
    }
  ],
  "fuera_de_la_lista": [
    {
      "id": "S1b-4-2026-03-03",
      "regla": "S1b",
      "grupo": 2,
      "prioridad": 0.0,
      "prueba": "CAC",
      "motivo": "CAC 120 mg/g (A2) el 2026-03-03, sin repetir en 8 meses y sin código de ERC",
      "pedido": "Albuminuria sin confirmar: repetir CAC en primera orina de la mañana",
      "nota": "CAC alterado sin confirmar (KDIGO 2024, PP 1.1.3.2 y 1.3.1.2): se solicita repetición en primera orina de la mañana (chorro medio); evitar durante la menstruación, tras ejercicio intenso o con infección urinaria sintomática o hematuria (tabla 16).",
      "fecha_origen": "2026-03-03",
      "person_id": 4,
      "nombre": "Antonio",
      "motivo_supresion": "Pedido ya pendiente: CAC solicitado el 2026-11-02",
      "sigue_en_lista": false
    }
  ],
  "baseline_fge_menor_60": [],
  "parametros": [
    {
      "clave": "cac_a3_mg_g",
      "valor": 300.0,
      "estado": "firmado",
      "fuente": "KDIGO 2024, tabla 1: A3 ≥300 mg/g"
    },
    {
      "clave": "cac_a3_mg_mmol",
      "valor": 30.0,
      "estado": "firmado",
      "fuente": "KDIGO 2024, tabla 1: A3 ≥30 mg/mmol"
    },
    {
      "clave": "cac_umbral_mg_g",
      "valor": 30.0,
      "estado": "firmado",
      "fuente": "KDIGO 2024, tabla 1: A2 30–299 mg/g"
    },
    {
      "clave": "cac_umbral_mg_mmol",
      "valor": 3.0,
      "estado": "firmado",
      "fuente": "KDIGO 2024, tabla 1: «ACR ≥30 mg/g [≥3 mg/mmol]»"
    },
    {
      "clave": "caida_aislada_pct",
      "valor": 20.0,
      "estado": "firmado",
      "fuente": "KDIGO 2024, PP 2.1.3"
    },
    {
      "clave": "caida_categoria_pct",
      "valor": 25.0,
      "estado": "firmado",
      "fuente": "KDIGO 2012, rec. 2.1.3"
    },
    {
      "clave": "dias_revision",
      "valor": 30.0,
      "estado": "firmado",
      "fuente": "Decisión de diseño: fecha de revisión del resultado"
    },
    {
      "clave": "fge_max_plausible",
      "valor": 200.0,
      "estado": "firmado",
      "fuente": "Vuelta 13 (Ahmed, 16 nov 2026), R6: un FGe ≤0 o >200 es imposible → información insuficiente. Comprobación de datos"
    },
    {
      "clave": "meses_dm1_cribado",
      "valor": 60.0,
      "estado": "firmado",
      "fuente": "Vuelta 13 (Ahmed, 16 nov 2026), D: DM1 entra en el cribado 5 años después del primer código E10. Consenso ADA–KDIGO 2022 (Diabetes Care, doi:10.2337/dci22-0027): «For T1D, screening is recommended commencing 5 years after diagnosis»"
    },
    {
      "clave": "meses_embarazo",
      "valor": 10.0,
      "estado": "firmado",
      "fuente": "Vuelta 13 (16 nov 2026), R2: un código O (embarazo) excluye si empezó en los últimos 10 meses. Decisión de diseño (la firma dice «embarazo», no da ventana)"
    },
    {
      "clave": "meses_inicio_farmaco",
      "valor": 3.0,
      "estado": "firmado",
      "fuente": "KDIGO 2024, PP 2.1.4"
    },
    {
      "clave": "meses_min_tendencia",
      "valor": 12.0,
      "estado": "firmado",
      "fuente": "Decisión de diseño"
    },
    {
      "clave": "meses_nota_realizada",
      "valor": 12.0,
      "estado": "firmado",
      "fuente": "N1f (Ahmed, 14 nov 2026): una prueba hecha según una nota cuenta 12 meses, como el cribado anual de S1a. Decisión de diseño"
    },
    {
      "clave": "meses_pedido_vigente",
      "valor": 3.0,
      "estado": "firmado",
      "fuente": "Decisión de diseño: un pedido de más de 3 meses sin resultado ya no suprime"
    },
    {
      "clave": "meses_persistencia_cac",
      "valor": 3.0,
      "estado": "firmado",
      "fuente": "N1a enmendada (Ahmed, 14 nov 2026): dos CAC alterados separados ≥3 meses = persistente (KDIGO 2024, cronicidad de al menos 3 meses)"
    },
    {
      "clave": "meses_sin_cac",
      "valor": 12.0,
      "estado": "firmado",
      "fuente": "PROT-AP ERC 2025: cribado anual con FGe y CAC"
    },
    {
      "clave": "meses_sin_repetir_cac",
      "valor": 6.0,
      "estado": "firmado",
      "fuente": "Decisión de diseño (la guía no da cifra)"
    },
    {
      "clave": "meses_ventana_fge",
      "valor": 36.0,
      "estado": "firmado",
      "fuente": "Decisión de diseño: solo FGe de los últimos 36 meses entran en la tendencia"
    },
    {
      "clave": "pendiente_fge",
      "valor": -5.0,
      "estado": "firmado",
      "fuente": "KDIGO 2012, rec. 2.1.3"
    }
  ]
};

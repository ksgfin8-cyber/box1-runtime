# BOX1-R01 · Caracterización y verificación inicial de BOX1-RUNTIME

**Registro:** v1 · 21 de noviembre de 2026  
**Norma operacional:** RDL-PB-001 v0.1 (sin modificación)  
**Línea base:** `ksgfin8-cyber/box1-runtime@d207bc714a3a027270f375fb54d5df25869cbcd3`  
**Alcance:** fuentes en Git, módulo de captura Python, adaptador, contrato HTTP y simulación aislada de persistencia.  
**Estado:** investigación inicial cerrada para los interrogantes locales; integración real con MongoDB, despliegue y transferencia: NO EVALUADOS.  
**Producto:** documento de investigación, sin modificación del comportamiento del repositorio.

## 1. Autoridad, método y admisión

El marco normativo es `docs/program/RDL-PB-001_v0.1_original_propuesta.md`. M1–M7 se usan únicamente como modos metodológicos auxiliares, no como etapas ni normas del Playbook. Se seleccionan M1, M2, M3, M4, M5 y M6; M7 se aplica sobre las limitaciones de los instrumentos. Las preguntas, evidencia, límites y decisiones siguen los §§3–14, 19–20 y 23 del Playbook.

**Objeto:** implementación Python de un capturador de señales con adaptador y endpoint FastAPI; identidad fijada por commit. **Especificación canónica separada del código:** no encontrada en el árbol estudiado. Las frases del código «Frozen. No redesign», «any input», «No rejection», «No interpretation», «No validation», «Normalize (structural only, idempotent)», «Persist verbatim (NO mutation)» y «Return CanonicalSignal exactly» se consideran reclamaciones de implementación, no contratos normativos acreditados.

**Inventario completo:** `README.md` (título únicamente), `backend/.env.example`, `backend/requirements.txt`, `backend/server.py`, `boxes/box1_capture/__init__.py`, `boxes/box1_capture/capture.py`, `layer1/adapters/__init__.py`, `layer1/adapters/box1_adapter.py`, y el Playbook incorporado. No se identificó una batería de pruebas ni un contrato de despliegue en el árbol. El historial disponible comienza el 5 de febrero de 2026, con múltiples cambios al servidor ese día, y añade el Playbook el 21 de noviembre de 2026. Este último es retrospectivo y no se atribuye a la implementación de febrero.

## 2. Arquitectura y mecanismo observado (M1, M3)

`POST /api/capture` → validación/deserialización de FastAPI/Pydantic → `call_box1()` → `capture()` → `CanonicalSignal` → `db.box1_signals.insert_one(signal)` → respuesta HTTP.

La función captura un objeto Python por referencia, etiqueta `encoding` como `utf-8` para cadenas, `binary` para bytes y `unknown` para los demás tipos; construye un timestamp UTC y fija `flags.malformed=False`, `flags.complete=True`. Escribe en stdout representación, hora y etiqueta de origen. No realiza interpretación de contenido. La ausencia de transformación no equivale a copia inmutable, serialización canónica o fidelidad de almacenamiento.

El adaptador `layer1/adapters/box1_adapter.py` es una delegación directa de una llamada; no existe transformación ni verificación adicional. El servidor depende de variables `MONGO_URL`, `DB_NAME` y eventualmente `CORS_ORIGINS`. `backend/.env.example` solo incluye `PORT` y `DEBUG`, no las dos claves exigidas para el arranque. Las librerías de `requirements.txt` son numerosas frente al módulo investigado y combinan versiones fijadas con mínimos; no se cuantificó su coste de instalación ni se verificó compatibilidad de todo el conjunto.

## 3. Preguntas y criterios de cierre (§6)

| ID | Pregunta | Criterio discriminativo | Uso de decisión |
|---|---|---|---|
| BQ1 | ¿Qué datos captura `capture()` sin transformación de valor? | Muestras de tipos y comparación de identidad/igualdad | Delimitar alcance del núcleo |
| BQ2 | ¿La representación completa es idempotente e inmune a mutación posterior? | `capture(capture(x))` y modificación externa de datos mutables | Validez de propiedades declaradas |
| BQ3 | ¿La garantía alcanza la superficie HTTP? | Solicitudes JSON válidas, incompletas, mal tipadas y malformadas | Distinguir capas y tipos admitidos |
| BQ4 | ¿La persistencia y recuperación conservan toda la entrada? | Prueba de integración MongoDB real e ida/vuelta | Condicionar reclamación end-to-end |
| BQ5 | ¿Qué elemento es transferible y bajo qué condiciones? | Contrato explícito por tipo, canal y ciclo de vida | Reutilización/decisiones |
| BQ6 | ¿Qué capacidad metodológica se obtiene? | Instrumentos que discriminan afirmaciones del núcleo y del transporte | Conservación de protocolo |

**Presupuesto y escalamiento:** primero inspección estática y pruebas locales, luego simulación HTTP. No se asignó infraestructura externa ni se realizaron escrituras a servicios de terceros. Se detiene al discriminar los reclamos relevantes dentro de este alcance; prueba real MongoDB requiere autorización, configuración y criterios propios.

## 4. Protocolos y ejecuciones (§§7–10)

**P0/v1 — Auditoría de árbol e historial.** Inspección de todos los nueve archivos (incluido Playbook) y historial de commits. Resultado: no hay tests de producto en el árbol; `capture.py` es el núcleo y `server.py` introduce restricciones de transporte y persistencia; las afirmaciones de congelación no están respaldadas por una especificación canónica separada.

**P1/v1 — Captura local con el archivo productivo.** Se ejecutó una copia de `boxes/box1_capture/capture.py` verificada byte a byte por SHA Git `cd8c75a7cfa205bc18936bd4a98218584e0b5be3`. Python ejecutó las funciones sin alterar la fuente. Entradas: texto Unicode con NUL, texto vacío, entero, booleano, `None`, diccionario con lista, lista, bytes `00 ff 01` y `set`. Se comprobó identidad de `raw_payload`, `encoding`, serialización mediante `json.dumps`, contenido y stdout.

Resultados: las nueve llamadas devolvieron registro; las nueve entradas conservaron identidad de `raw_payload` en memoria. Para `bytes` y `set`, `json.dumps(record)` devolvió `TypeError`. Los otros siete casos de la matriz fueron serializables como JSON por el serializador estándar. Estos son casos seleccionados, no una prueba exhaustiva de todos los tipos Python.

**P2/v1 — Contraejemplos de propiedades.** Tras capturar un diccionario mutable, agregar un elemento a una lista del objeto de origen alteró lo observado en `raw_payload`; el registro conserva referencia, no una instantánea inmutable. `capture(capture('abc'))` no es igual a `capture('abc')`: cambia la envoltura y se produce nuevo timestamp. La afirmación de idempotencia de la «normalización» podría referirse únicamente a la asignación `canonical_form=signal_blob`, pero **no** al proceso completo; el documento de origen no define formalmente esa distinción. Las banderas `malformed=False` y `complete=True` son constantes, no resultados de validación de integridad o completitud.

**P3/v1 — Ensayo HTTP con dependencias simuladas.** Se ejecutó una copia de `backend/server.py` con SHA Git verificado `670be86b35efe32e2f2b3c0c8c067d9b51d715f6` y adaptador con SHA `df1a482100f39ef87ce514083964549003959566`. Se usó FastAPI `0.128.2`, Pydantic `2.13.5`, `TestClient` y una implementación ficticia de `AsyncIOMotorClient`/colección con `insert_one`, **no MongoDB real**. La versión de FastAPI de este ensayo **difiere** de la fijada en `requirements.txt` (`0.110.1`).

Casos HTTP: texto, diccionario, texto vacío, `null` → cuatro respuestas `200` y cuatro llamadas al doble de inserción; cuerpo sin `raw_input`, `source_tag` numérico y JSON malformado → tres respuestas `422`, sin invocar captura. La respuesta acepta `null` y declara `flags.complete=True`, lo cual no prueba completitud semántica. La implementación del doble almacena una copia superficial sin mutar el objeto; por diseño **no verifica** la conducta de `insert_one` del driver real, fallo de DB, BSON, rollback, readback, latencia ni concurrencia. Tampoco prueba que los bytes puedan enviarse por JSON sin representación alternativa.

**Reproducibilidad:** P1/P2 pueden repetirse importando `capture` desde el commit fijado y probando los casos listados. P3 requiere sustituir `motor.motor_asyncio.AsyncIOMotorClient` por una clase que proporcione `__getitem__` e `insert_one` asíncrono; configurar `MONGO_URL` y `DB_NAME` ficticios; crear `TestClient(app, raise_server_exceptions=False)`; enviar la matriz. No se conservó un harness estable en el repositorio porque las pruebas fueron puntuales y el alcance no autoriza modificar productos. Los resultados de P3 están condicionados por sus dependencias diferentes. La ejecución independiente bajo el entorno fijado del producto continúa NO EVALUADA.

## 5. Evaluación de afirmaciones y límites (§11, §19)

| Claim | Resultado / estado | Alcance |
|---|---|---|
| `capture()` acepta los nueve objetos Python ensayados | OBSERVADO | Solo P1; sin generalización a todos los objetos |
| El valor se copia sin pérdida | NO DEMOSTRADO | Hay retención por referencia en memoria, no snapshot ni transporte end-to-end |
| La captura completa es idempotente | EVIDENCIA CONTRARIA | P2 exhibe nueva envoltura y timestamp |
| `CanonicalSignal` es universalmente serializable como JSON | EVIDENCIA CONTRARIA | Bytes y set generan TypeError en `json.dumps` |
| La API no rechaza ninguna entrada | EVIDENCIA CONTRARIA | FastAPI devuelve 422 antes de invocar el núcleo en P3 |
| `flags` son constataciones de integridad/completitud | NO ESTABLECIDO | Valores constantes sin evaluación de contenido |
| Persistencia literal y recuperación sin pérdida | NO EVALUADO | No se ejecutó MongoDB ni lectura de vuelta |
| Timestamp determinista de una entrada | EVIDENCIA CONTRARIA | Depende del reloj |
| Reutilización interdominio | NO EVALUADO | Un único sistema y ningún receptor externo |

**Riesgos localizados:** captura por referencia de objetos mutables; afirmaciones de normalización e idempotencia mal delimitadas; discrepancia entre tipos Python y dominio JSON; semántica no validada de las banderas; stdout con representación del contenido (posible filtración según sensibilidad); rutas de error externo no caracterizadas; variables obligatorias ausentes de `.env.example`; ausencia de tests integrados; trazabilidad de copia/persistencia sin oráculo de ida y vuelta. Estos riesgos son hipótesis de impacto o límites sustentados por el código; no todos son defectos contractuales hasta determinar requerimientos aplicables.

## 6. Capacidad, transferencia y economía (M6–M7, §§12, 14–17)

**Activo identificable:** pequeña función de envoltura temporal y etiquetado, con un adaptador que conserva la llamada. **Transferencia potencial:** a un consumidor de objetos Python en memoria bajo requisitos que acepten referencias y metadatos por reloj. Requiere revalidación para objetos mutables, persistencia BSON, clientes HTTP, identidad, codificación binaria y recuperación. No está demostrado que el nombre `CanonicalSignal` represente una canonización semántica o binaria independiente del lenguaje.

**Activo metodológico:** protocolo de contraste por capas (objeto Python → transporte JSON → persistencia → recuperación), con controles negativos sobre tipos, mutabilidad, serialización e idempotencia. Está ejecutado localmente en Python y HTTP simulado, pero no transferido ni medido contra otros proyectos. No se dispone de horas históricas, coste de operación, throughput o benchmark; productividad y costes NO EVALUADOS.

## 7. Decisiones de ingeniería (§13)

1. **Aceptar M1/M3 como caracterización inicial:** flujo y restricciones identificables. No implica conformidad con una especificación técnica independiente.
2. **No aceptar la proposición fuerte «captura arbitraria, inmutable y sin pérdida a través de toda la pila»:** no está demostrada y algunas formulaciones naturales son contradichas por P1–P3.
3. **No aplicar correcciones de producto durante esta investigación:** primero se requiere decisión del propietario sobre dominio de entradas, sentido de «sin pérdida», idempotencia y semántica de `complete/malformed`.
4. **No certificar la integración real:** condicionar evaluación posterior a requerimientos de persistencia, credenciales de prueba, versiones de dependencias y un oráculo de ida y vuelta.
5. **Conservar el mecanismo y la investigación como antecedentes:** no autorizar despliegue, integración o eliminación del activo con estos resultados exclusivamente.

Son recomendaciones fundamentadas, no decisiones de implementación autorizadas.

## 8. Cierre, incertidumbre y reapertura (§23)

**Cierre del estudio inicial local:** completados inventario, caracterización estructural, examen de afirmaciones, contraejemplos controlados y análisis de transferencia potencial. Quedan NO EVALUADOS: MongoDB real; serialización BSON y readback; fidelidad de una entrada binaria mediante HTTP; fallos y recuperación; seguridad, concurrencia, rendimiento, despliegue y valor de negocio. No se confunden con una campaña incumplida.

**Reabrir si:** se establece contrato técnico de `CanonicalSignal`; se define el dominio de entrada del sistema; una decisión de integración necesita garantías de persistencia; existe un receptor concreto para transferencia; aparece evidencia operacional que altera el dictamen.

**Verificación posterior:** las pruebas positivas y negativas no prueban universalidad; la ejecución de servidor utiliza dobles y versiones diferentes; no se modificó código, datos externos ni Playbook. El siguiente coste experimental solo se justifica ante una decisión que pueda cambiar.

**Dictamen:** caracterización inicial GO; reclamaciones fuertes de fidelidad end-to-end NO VERIFICADAS y parcialmente contradichas; continuación de I+D condicionada a preguntas contractuales y decisiones explícitas.

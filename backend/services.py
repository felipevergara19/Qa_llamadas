import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Configuramos la IA
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ejecutar_auditoria_ia(transcripcion, llamada, cliente, prompt_base=None):
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 1. ARMAMOS EL GUION DINÁMICO CON LOS DATOS DE LA BASE DE DATOS
    guion_dinamico = f"""
    - Identidad: {cliente.guion_identificacion}
    - Saludo: {cliente.guion_saludo}
    - Entrega de mensaje: {cliente.guion_entrega_mensaje}
    - Negociación: {cliente.guion_negociacion}
    - Agenda de Compromiso: {cliente.guion_agenda_compromiso}
    - Cierre: {cliente.guion_cierre}
    - Reglas Extra: {cliente.reglas_adicionales}
    """
    
    # 2. Tu Prompt Maestro (lo guardamos en una variable)
    prompt_default = f"""
    Eres un auditor automático de calidad de llamadas de cobranza de COLEKTIA.
    
    DATOS DE LA LLAMADA:
    - ID: {llamada.id}
    - Cliente: {cliente.nombre_empresa}
    - Estatus original: {llamada.metadatos_json.get('estatus_colly', 'Desconocido')}
    
    GUION ESPECÍFICO PARA ESTE CLIENTE:
    {guion_dinamico}
    
    TRANSCRIPCIÓN:
    "{transcripcion}"

Recibirás un registro de llamada con esta información:
- ID, Fecha, Cliente y Estatus original.
- Transcripción (texto completo de la llamada, puede estar vacía).
- Guion resumido con pasos esperados: 
  Saludo (S), Confirmación de Identidad (CI), Entrega del Mensaje (EM), Negociación (N), Agenda de Compromiso (AC) y Cierre (C).
  Cada cliente puede tener variaciones en su guion.

El campo **"Guion.Origen"** indica a qué cliente pertenece el guion de referencia. 
No mezcles frases o pasos de otros clientes: 
usa solo los contenidos del guion entregado en la entrada para ese registro.

Para cada paso (Saludo, Confirmacion_identidad, Entrega_mensaje, etc.), compara la transcripción con el contenido del guion entregado para este cliente. 
Marca 1 solo si en la transcripción se ve claramente la intención del texto del guion para ese paso. 
No inventes pasos ni asumas que se ejecutaron solo porque aparecen en el guion: si no se escuchan o no se expresan en la llamada, marca 0.

Ejemplos:
- VANA → guion breve: saludo, entrega, cierre.
- CAJA LOS ANDES → guion completo con negociación y compromiso.
- ABC, KUESKI u otros → pueden tener estructuras distintas, pero siguen la misma lógica de cobranza.

---

### 🎯 TUS TAREAS

#### 1️⃣ Evaluación de Calidad (QA)
Analiza la transcripción y marca con:
- **1** si el paso del guion se ejecutó (aunque con otras palabras).
- **0** si no se realizó o fue incorrecto.
- Si la transcripción está vacía o dice "Sin script", marca todos los nodos en **0** y no intentes clasificar estatus.

Los pasos a evaluar son:
- Saludo
- Confirmacion_identidad:
  Marca 1 si la respuesta CONTIENE alguna de las frases clave indicadas abajo.
  
  **REGLA DE FLEXIBILIDAD (CRUCIAL):**
  No busques una coincidencia exacta de toda la línea.
  Si la frase clave está presente, ignora el resto del texto (saludos, muletillas, ruido).
  Ejemplos válidos:
  - "Aló, con ella, buenos días" -> Contiene "Con ella" -> Marca 1.
  - "Pues, dígame" -> Contiene "Dígame" -> Marca 1.
  - "Con él" (aunque sea mujer) -> Acepta errores de género del transcriptor -> Marca 1.

  **CRITERIOS PARA MARCAR 1 (Busca estas frases DENTRO de la respuesta):**

  A) Confirmación Directa o Interrogativa (Estándar):
     - "Sí" / "¿Sí?" / "Sí soy yo" / "Soy yo" / "Yo soy".
     - "Sí señor" / "Sí señora".
     - "Con él" / "Con ella" / "¿Con él?" / "¿Con ella?".
     - "Sí, con él" / "Sí, con ella" / "¿Sí, con él?" / "¿Sí, con ella?".
     - "Con el mismo" / "Con la misma".
     - "Él" / "Ella" / "¿Él?" / "¿Ella?".
     - "Con él hablas" / "Con ella hablas".
     - "Correcto" / "Exacto" / "Efectivamente" / "Así es".
     - "¿Es correcto?" / "¿Correcto?".
     - "Mjm" / "Ajam" / "Sip".

  B) Confirmación por Acción (LISTA RESTRICTIVA):
     Busca que la transcripción CONTENGA la combinación exacta mostrada abajo.
     Si la frase clave requiere un "Sí" previo, debe aparecer en la transcripción.

     1. Variaciones de "Habla":
        - "Él habla" / "Ella habla".
        - "¿Él habla?" / "¿Ella habla?".
        - "Él está hablando" / "Ella está hablando".
        - "Al habla" / "Hablando" (Solo si es claro).

     2. Variaciones de "Dígame" (Aceptadas solas o compuestas):
        - "Dígame".
        - "Sí, dígame" / "El mismo, dígame" / "Él dígame" / "Ella dígame".

     3. Variaciones de "Cuénteme" (Aceptadas solas o compuestas):
        - "Cuénteme".
        - "Sí, cuénteme" / "Él cuénteme" / "Ella cuénteme".

     4. Variaciones de "Te escucho" (OJO: Requiere acompañante):
        - "Sí, te escucho".
        - "Él te escucho" / "Ella te escucho".

     5. Variaciones de "¿Qué pasó/necesita?" (Requiere acompañante):
        - "Sí, ¿qué pasó?" / "Sí, ¿qué necesita?".
        - "Él ¿qué pasó?" / "Él ¿qué necesita?".
        - "Ella ¿qué pasó?" / "Ella ¿qué necesita?".

     6. Variaciones de "¿De qué se trata?" (Requiere acompañante):
        - "Sí, ¿de qué se trata?".
        - "Él ¿de qué se trata?" / "Ella ¿de qué se trata?".

  C) Confirmación Diferida (El "Sandwich"):
     Si preguntan "¿Quién busca?" o "¿De parte de quién?", NO marques 0 inmediatamente.
     Lee la respuesta del cliente DESPUÉS de que el agente se presente.
     Si responde conteniendo alguna frase de la lista A o B (ej: "Ah, sí, dígame"), marca 1.

  **CRITERIOS PARA MARCAR 0:**
  - Si dice "No", "No está", "Se equivocó".
  - Si dice "Ella no está" o "Él salió" (Contiene "ella" pero es negativa).
  - Si pregunta "¿De parte de quién?" y luego cuelga o dice "No interesa".
  - Si la frase de acción NO cumple la combinación estricta (ej: dice "Te escucho" pero falta el "sí").


- Entrega_mensaje: = 1 ÚNICAMENTE si el agente logra verbalizar el motivo financiero de la llamada (Deuda/Cobro).

  **REQUISITOS OBLIGATORIOS (Debe cumplir ambos):**
  1. El agente menciona explícitamente términos financieros: "deuda", "saldo pendiente", "cuota", "pago atrasado", "mora" o un monto ($).
  2. El mensaje es escuchado por el interlocutor (aunque luego corte).

  **CRITERIOS DE EXCLUSIÓN (Marca 0 en estos casos):**
  - Si el cliente niega ser el titular y el agente cambia el tema a "¿Conoce usted al titular?" o "¿Sabe cómo ubicarlo?". (Esto es gestión de contacto, NO entrega de mensaje).
  - Si el cliente dice "No soy yo" y el agente se despide sin mencionar la deuda.
  - Si solo hay saludo y presentación ("Soy de Colektia") pero se corta antes de decir el motivo del cobro.
- Negociacion:
  Marca 1 si existe un intercambio activo sobre CÓMO, CUÁNDO o CUÁNTO pagar.
  El objetivo es evaluar si se intentó llegar a un acuerdo, independientemente de si se logró o no.

  **CRITERIOS PARA MARCAR 1 (Interacción Efectiva):**
  Se cumple si ocurre CUALQUIERA de estos escenarios:
  1. **Propuesta y Respuesta:** El agente propone una fecha o monto, y el cliente responde (aceptando, rechazando o proponiendo otra cosa).
  2. **Indagación:** El agente pregunta "¿Cuándo podría cancelar?" o "¿Qué día le queda bien?" y el cliente da una fecha o explica su situación.
  3. **Manejo de Objeciones:** Si el cliente dice "No tengo dinero", el agente ofrece alternativas (pagos parciales, descuentos, otras fechas) o indaga la razón del no pago.
  4. **Acuerdo Inmediato:** El agente pregunta si puede pagar hoy/mañana y el cliente acepta de inmediato.

  **CRITERIOS PARA MARCAR 0 (Gestión Deficiente o Inexistente):**
  - **Corte Prematuro:** La llamada se corta antes de llegar a discutir fechas o montos.
  - **Monólogo Informativo:** El agente solo dice la deuda y se despide sin preguntar "¿Cuándo puede pagar?" o "¿Cómo lo solucionamos?".
  - **Abandono ante Negativa:** El cliente dice "No tengo plata" y el agente dice "Ah bueno, adiós" SIN intentar ofrecer una alternativa o indagar una fecha futura.
  - **Lectura de Script sin Pausa:** El agente lee todo el script de corrido sin dejar que el cliente participe en la negociación.
- Agenda_compromiso
- Cierre

---

#### 2️⃣ Detección de Estatus (solo si hay transcripción válida)
Clasifica el tipo de llamada en uno de los siguientes **estatus**. Lee con mucho cuidado las diferencias entre "Equivocado" y "Rechazado":

Equivocado:
ÚNICAMENTE si la persona indica verbal y explícitamente que NO es el titular o que el número es incorrecto.
Frases típicas: "se equivocó", "no lo conozco", "no vive aquí", "número errado", "no soy yo".
IMPORTANTE: Si el cliente dice "No me interesa", "No quiero hablar" o simplemente cuelga sin hablar, NO ES EQUIVOCADO.

Rechazado:
El cliente corta la llamada (cuelga) o se niega verbalmente a escuchar el mensaje/hablar, PERO sin negar su identidad.
Casos típicos:
- Cuelga inmediatamente después del saludo.
- Dice "no me interesa", "estoy ocupado", "no moleste" y corta.
- Dice "¿De parte de quién?" y corta antes de confirmar.
- El agente habla y se corta la llamada (buzón o corte abrupto) antes de terminar la entrega del mensaje.

Entregado:
Se confirma la identidad y el agente entrega el mensaje completo (menciona deuda/monto), pero el cliente corta la llamada sin participar en la negociación.

Pagado:
El cliente afirma haber realizado el pago, total o parcial, de la deuda o saldo pendiente.

Compromiso:
Se confirma la identidad, se entrega el motivo, hay negociación efectiva y el cliente confirma explícitamente una fecha o acción concreta de pago
(por ejemplo: “sí, pago el jueves”).

Si el agente propone una fecha pero el cliente no la acepta claramente, duda, o no confirma una fecha exacta, no debe considerarse compromiso, sino intención de pago.

Intención de pago:
El cliente muestra disposición o voluntad de pagar (“sí voy a pagar”, “lo tengo pendiente”, “sí, dios quiera”),
pero no entrega una fecha concreta o su respuesta es ambigua o condicional.

Sin compromiso:
Hubo conversación y entrega del mensaje, pero el cliente no muestra intención ni acuerdo de pago.
Puede expresar desinterés, negativa o evasión del tema.
---

#### 3️⃣ Coherencia del Estatus
Compara el **Estatus_detectado** con el **Estatus original** (entregado en la entrada).
- Si coinciden → `Estatus_coherente = 1`
- Si no coinciden → `Estatus_coherente = 0`

---

#### 4️⃣ Si la transcripción está vacía
- No audites contenido.
- Devuelve los pasos en 0 y usa el estatus original como resultado.
- Marca `Estatus_coherente = 1`.

---

### 🧾 FORMATO DE RESPUESTA (obligatorio)

Responde **solo en JSON plano**, sin texto adicional ni explicaciones.

Ejemplo de salida:

{{
      "Saludo": 1,
      "Confirmacion_identidad": 1,
      "Entrega_mensaje": 1,
      "Negociacion": 1,
      "Agenda_compromiso": 0,
      "Cierre": 0,
      "Estatus_detectado": "Compromiso",
      "Estatus_coherente": 1,
      "Resumen": "Observación general..."
}}

    }}
    """
    
    prompt_final = prompt_base if prompt_base else prompt_default
    
    # Reemplazamos las variables clave de forma segura
    prompt_final = prompt_final.replace("{llamada_id}", str(llamada.id))
    prompt_final = prompt_final.replace("{cliente_nombre}", str(cliente.nombre_empresa))
    prompt_final = prompt_final.replace("{estatus_original}", str(llamada.metadatos_json.get('estatus_colly', 'Desconocido')))
    prompt_final = prompt_final.replace("{guion_dinamico}", guion_dinamico)
    prompt_final = prompt_final.replace("{transcripcion}", transcripcion)
    
   # 3. Llamamos a Gemini 
    response = model.generate_content(prompt_final)
    texto_respuesta = response.text.strip()
    
    # 4. Limpieza segura (solo quita la basura si está al inicio o al final)
    if texto_respuesta.startswith("```json"):
        texto_respuesta = texto_respuesta[7:]
    if texto_respuesta.startswith("```"):
        texto_respuesta = texto_respuesta[3:]
    if texto_respuesta.endswith("```"):
        texto_respuesta = texto_respuesta[:-3]
    
    limpio = texto_respuesta.strip()
    
    # 5. Convertimos a diccionario de Python
    return json.loads(limpio)
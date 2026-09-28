# 🏢 Edificio Rosario del Solar - Control Automatizado de Agua y Mantenimiento

Sistema 100% gratuito desarrollado con **Google Gemini con Visión por IA (3.8 Flash / 3.6 Flash)** y **Streamlit** para eliminar la digitación manual y la creación de diapositivas en el cobro de agua y mantenimiento mensual.

---

## 🚀 ¿Cómo usarlo en tu computadora? (1 Clic)

1. En tu **Escritorio**, haz doble clic en el archivo:
   👉 **`Iniciar_Control_Agua.bat`**
2. Se abrirá automáticamente la aplicación en tu navegador web (`http://localhost:8501`).
3. Ingresas el monto de Sedapal (ej. `S/ 974.60`), subes las fotos tomadas por Marlitt (o su archivo PowerPoint si ya lo tiene).
4. La Inteligencia Artificial lee los contómetros, calcula el prorrateo de agua y el mantenimiento de cada departamento.
5. Puedes hacer clic en **"Guardar en Excel Oficial"**, **"Archivar Fotos"** o copiar los mensajes de **WhatsApp** para los vecinos.

---

## 📱 ¿Cómo desplegarlo en la Nube GRATIS para el celular de Marlitt?

Para que Marlitt pueda entrar desde su propio teléfono (en la calle o el edificio) con un enlace público permanente sin que tu PC esté encendida:

1. Crea una cuenta gratuita en [GitHub](https://github.com/) (si no tienes una).
2. Crea un repositorio llamado `edificio-rosario` y sube los archivos de esta carpeta:
   - `app.py`
   - `config.py`
   - `requirements.txt`
   - Carpeta `core/`
3. Entra a [Streamlit Community Cloud](https://share.streamlit.io/) e inicia sesión con tu cuenta de GitHub.
4. Haz clic en **"New app"**, selecciona tu repositorio `edificio-rosario` y el archivo `app.py`.
5. En la sección **Advanced settings** -> **Secrets**, agrega tu API Key de Gemini:
   ```toml
   GEMINI_API_KEY = "AQ.Ab8RN6JyRyJFw6BLRIYIPW0fLZn_2DLLDYGpsSt7WkER9J0S2g"
   ```
6. Haz clic en **"Deploy"**. En 2 minutos tendrás una URL pública y gratuita (ejemplo: `https://edificio-rosario.streamlit.app`) para compartir con Marlitt.

---

## 🤖 Inteligencia Artificial y Modelos

- **Modelo Primario:** `gemini-3.8-flash` (Último modelo de alta velocidad y precisión).
- **Fallback Automático Inteligente:** `gemini-3.6-flash`. Si los servidores de vista previa de 3.8 están saturados (error 503 o timeout), el sistema conmuta automáticamente a 3.6 en milisegundos para que la lectura nunca falle.
- **Costo:** **$0.00** de por vida utilizando la cuota gratuita de Google AI Studio.

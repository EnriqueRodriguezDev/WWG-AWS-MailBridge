# Collection: MailBridge WorldWide Group & AWS SQS SES Service

Esta colección de Postman facilita la interacción con la API MailBridge, un servicio diseñado para la gestión de credenciales AWS, optimización y carga de documentos PDF a S3, y el encolamiento de correos electrónicos en SQS para su envío a través de SES.

## Descripción General

La API MailBridge automatiza un flujo de trabajo crucial que incluye:
* **Gestión de Credenciales**: Almacena y administra de forma segura las credenciales de AWS (claves, nombres de bucket, colas SQS) y credenciales JWT para autenticación.
* **Procesamiento de Archivos**: Permite la carga de archivos binarios (BLOB), optimizando automáticamente los PDFs antes de subirlos a un bucket S3 específico.
* **Envío de Correos Electrónicos**: Encola mensajes de correo electrónico con soporte HTML y múltiples adjuntos (via URLs de S3) en una cola SQS para su procesamiento asíncrono y envío a través de Amazon SES.

## Estructura de la Colección

La colección está organizada en los siguientes módulos principales:

### 1. Authentication & Health Check
Este módulo contiene las operaciones fundamentales para la autenticación y verificación del estado de la API MailBridge.

* **1. Obtener Token JWT (`/api/v1/login`)**: Valida las credenciales de usuario y base de datos para retornar un JSON Web Token (JWT) válido. Este token se guarda automáticamente en la variable de entorno `token` para su uso en solicitudes posteriores.
* **Health Check (`/health`)**: Un endpoint simple para verificar la salud y disponibilidad de la API.

### 2. File Upload & Email Sending
Este es el módulo operativo principal, que maneja la subida de archivos y el envío de correos electrónicos.

* **2. Subir Archivo Raw BLOB (`/api/v1/upload-raw-blob`)**: Recibe el contenido binario de un archivo directamente en el cuerpo de la solicitud HTTP. Los archivos (especialmente PDFs) son optimizados y subidos a AWS S3. Se requiere autenticación JWT.
* **3. Enviar Email con HTML (`/api/v1/send-email`)**: Envía un correo electrónico completo con cuerpo HTML (o texto plano) y la capacidad de adjuntar archivos pre-subidos a S3 (mediante sus URLs). Esta solicitud encola el mensaje en una cola SQS para su procesamiento asíncrono.

### 3. Credential Management
Este módulo administrativo permite la gestión completa de las credenciales y configuraciones de la API MailBridge.

* **Listar Credenciales AWS (`/api/v1/credentials/awsconf/`)**: Obtiene metadatos de las configuraciones de AWS almacenadas para una base de datos específica.
* **Actualizar Credenciales AWS (`/api/v1/credentials/awsconf/update`)**: Actualiza un valor específico de la configuración de AWS (e.g., `QUEUE_NAME`, `USR_SECRET`, `BUCKET_NAME`).
* **Listar Credenciales JWT (`/api/v1/credentials/mjwtcred/`)**: Obtiene metadatos de las credenciales de usuario de la API (username, password) utilizadas para la generación de tokens JWT.
* **Actualizar Credenciales JWT (`/api/v1/credentials/mjwtcred/update`)**: Actualiza las credenciales de usuario o contraseña para la autenticación de la API de MailBridge.

## Variables de Entorno

La colección utiliza las siguientes variables de entorno que deben configurarse en Postman:

* `urlbase`: La URL base de la API MailBridge.
    * **Desarrollo/Local**: `http://172.20.0.198:8000`
    * **Producción**: `http://172.20.0.198:8000/docs#/`
* `username`: Usuario para autenticación en la API.
* `password`: Contraseña para autenticación en la API.
* `token`: **No modificar manualmente.** Este valor se actualiza automáticamente después de una solicitud exitosa a `/api/v1/login`.
* `database`: Nombre de la base de datos a usar para las operaciones (ej. `SEGQA`, `WWMAQA`, `SEGWW`, `WWMA`).
* `filename_to_upload`: Nombre del archivo de ejemplo para la subida (ej. `example.pdf`). **¡Cambiar al nombre real de tu archivo local!**
* `id_proceso_for_upload`: ID de proceso de ejemplo para la subida de archivos (ej. `12345`).

## Flujo de Trabajo Recomendado

1.  **Configurar Variables**: Asegúrate de que las variables de entorno `urlbase`, `username`, `password`, `database`, `filename_to_upload` e `id_proceso_for_upload` estén configuradas correctamente para tu entorno.
2.  **Verificar Salud**: Ejecuta la solicitud "Health Check" para asegurar que la API está accesible.
3.  **Obtener Token**: Ejecuta la solicitud "1. Obtener Token JWT (`/api/v1/login`)". Esto autenticará tu sesión y guardará el token en la variable `token`.
4.  **Subir Archivos (Opcional)**: Si necesitas adjuntar archivos a tus correos, utiliza la solicitud "2. Subir Archivo Raw BLOB (`/api/v1/upload-raw-blob`)". Asegúrate de que la ruta local de tu archivo en `filename_to_upload` sea correcta en la configuración del `body` de la solicitud (modo `file`).
5.  **Enviar Correo**: Usa la solicitud "3. Enviar Email con HTML (`/api/v1/send-email`)". Puedes incluir las URLs S3 de los archivos subidos en el array `attachments` si es necesario.
6.  **Gestión de Credenciales (Administradores)**: Utiliza las solicitudes dentro del módulo "Credential Management" para listar o actualizar configuraciones de AWS o credenciales JWT.

## Notas Adicionales

* La colección maneja automáticamente la extracción y almacenamiento del token JWT.
* Las credenciales sensibles (AWS, JWT) se asumen encriptadas en la base de datos subyacente.
* La funcionalidad de subida de archivos está diseñada para procesar y optimizar PDFs antes de su almacenamiento en S3.
# ADR-0004: Identidad y acceso para HU-01/HU-02

**Estado:** implementada en ramas de trabajo, **pendiente de revisión cruzada e integración en `develop`**. El PR #35 del modelo de datos ya fue integrado; H04 sigue sujeto a validación de despliegue y de permisos de los módulos restantes.

## Contexto
El MVP requiere registrar tostadores, autenticar usuarios y preservar los límites de acceso
por organización. La base es FastAPI + SQLAlchemy + PostgreSQL y React + TypeScript.

## Decisión
1. Monolito modular con separación por capas (API → servicio de aplicación → ORM). No DDD táctico completo:
   no hay complejidad de dominio que justifique interfaces/repositorios artificiales.
2. Los esquemas Pydantic del PR #35 constituyen el contrato; no se cambian nombres ni rutas.
3. En registro se persisten organización y usuario en una transacción. Un índice UNIQUE
   de email evita duplicados concurrentes, además de la comprobación anticipada.
4. Contraseñas con Argon2id (`pwdlib[argon2]`); nunca texto plano.
5. JWT HS256 con secreto externo de al menos 32 caracteres, sub, iat y exp (8 horas).
   La firma se verifica con algoritmo permitido fijo. El servidor valida actividad del usuario
   en las rutas autenticadas; no basta con confiar en atributos del token.
6. El frontend mantiene el token en `sessionStorage`, lo elimina al cerrar sesión y
   valida `/auth/me` al restaurar la sesión. Esto reduce persistencia entre sesiones,
   pero NO previene robo de token mediante XSS; configurar CSP en hosting y evitar HTML inseguro.
7. El login devuelve un error genérico para credenciales incorrectas, evitando enumerar cuentas.

## Consecuencias y límites
- Ninguna ruta de negocio debe depender solo del control visual React: debe utilizar
  la dependencia `get_current_user` y validar rol y pertenencia en backend (HU-04).
- El cierre de sesión no revoca JWT ya emitidos: el contrato especifica borrado del lado
  cliente. Para revocación inmediata se necesitarían tokens de corta duración y/o blacklist.
- Antes de producción, añadir rate limiting en gateway, CSP, HTTPS, observabilidad y
  gestión de secretos. En ambientes públicos no usar el valor de ejemplo de JWT_SECRET_KEY.
- Antes de integrar el PR, confirmar las correcciones pedidas al PR #35; no aprobar
  automáticamente una migración por ejecutar estas HU.

## Origen de la decisión
- Project Charter §3.4 (alcance), §4.2.1 (ARQ-01/ARQ-02) y §12.1.3–12.1.4 (DoD y HU).
- `docs/arquitectura/README.md` y contrato `docs/api/contrato-api.md` propuesto en PR #35.
- Se conserva la estructura original del monorepo, sin alterar las ADR anteriores.

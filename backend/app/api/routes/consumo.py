"""EP-06 Historial de consumo: importación desde CSV o Excel (HU-18)."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import exigir_tostador
from app.db.session import get_db
from app.models.identidad import Usuario
from app.schemas.consumo import ImportacionOut
from app.services import consumo as servicio

router = APIRouter(prefix="/consumo-historico", tags=["consumo"])


@router.post("/importar", response_model=ImportacionOut)
async def importar(
    archivo: UploadFile, usuario: Usuario = Depends(exigir_tostador), db: Session = Depends(get_db)
) -> ImportacionOut:
    """HU-18: todo o nada. Con errores no se guarda ninguna semana y se devuelve cada fila con su problema."""
    contenido = await archivo.read(servicio.MAX_BYTES + 1)
    try:
        semanas, errores = servicio.leer_archivo(archivo.filename or "", contenido)
    except servicio.ArchivoDemasiadoGrande:
        raise HTTPException(status_code=413, detail="El archivo es demasiado grande (máximo 20 000 filas)") from None
    except servicio.ArchivoInvalido as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    if errores:
        return ImportacionOut(semanas_importadas=0, desde=None, hasta=None, errores=errores)
    servicio.guardar_semanas(db, usuario.organizacion_id, semanas)
    return ImportacionOut(semanas_importadas=len(semanas), desde=min(semanas), hasta=max(semanas), errores=[])

from fastapi import APIRouter, status, UploadFile, File, HTTPException
import tempfile
from api.exceptions.exceptions import UploadError
from api.repository.redis_repository import RedisConnection, RedisRepository
from api.schemas.packet_processor import UploadResult
from api.services.pcap_service import PacketPcapService

router = APIRouter(prefix="/packets", tags=["Packet Processor"])


@router.post("/upload-pcap", status_code=status.HTTP_202_ACCEPTED)
async def upload_pcap(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        packet_pcap_service = PacketPcapService(tmp_path, redis)
        try:
            result = await packet_pcap_service.upload_file()
        except UploadError:
            raise HTTPException(status_code=500)

    return UploadResult(**result.dict())

    # try:
    #     with tempfile.NamedTemporaryFile(delete=False) as tmp:
    #         content = await file.read()
    #         tmp.write(content)
    #         tmp_path = tmp.name
    #     bgt.add_task(process_pcap_in_background, tmp_path)
    #
    #     return {"message": "File uploaded and processing started"}
    #
    # except Exception as e:
    #     raise HTTPException(status_code=500)

# async def process_pcap_in_background(tmp_path: str):
#     try:
#         packet_service = PacketPcapService(tmp_path)
#         await packet_service.process_pcap_file()
#         os.unlink(tmp_path)
#     except Exception as e:
#         print(f"Error processing pcap: {e}")

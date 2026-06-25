from app.domain.data_management.repository import MasterDataRepository

class MasterDataService:
    def __init__(self, repo: MasterDataRepository):
        self._repo = repo

    async def list_by_type(self, data_type: str):
        return await self._repo.list_by_type(data_type)

    async def search(self, query: str):
        return await self._repo.search(query)

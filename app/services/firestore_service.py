from typing import Optional,Any

class FirestoreService:
    def __init__(self):
        self._dict:dict[str,dict[str,Any]]={}
    
    def save(self,task_id:str,data:dict[str,Any])-> None:
        self._dict[task_id] = data
    
    def get(self,task_id:str)->Optional[dict[str,Any]]:
        return self._dict.get(task_id)
    
    def get_all(self) -> list[dict[str, Any]]:
        return list(self._dict.values())
    
    def delete(self,task_id:str)->Optional[dict[str,Any]]:
        return self._dict.pop(task_id,None)
    
firestore_service = FirestoreService()
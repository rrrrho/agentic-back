from langchain_huggingface import HuggingFaceEmbeddings

def get_hugging_face_embedding(model_id: str, device: str) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=model_id,
        model_kwargs={'device': device, 'trust_remote_code': True},
        encode_kwargs={'normalize_embeddings': False},
    )

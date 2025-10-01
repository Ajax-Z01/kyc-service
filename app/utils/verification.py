from typing import Tuple, Dict

def verify_document_advanced(parsed_fields: Dict[str, str]) -> str:
    """
    Verifikasi dokumen berdasarkan hasil parsing KTP.
    
    Args:
        parsed_fields: dict hasil parsing KTP (misal dari parse_ktp_fields)
    
    Returns:
        status: "Verified", "Manual Review", atau "Rejected"
    """
    
    # --- Hitung jumlah field penting yang valid ---
    required_fields = ['NIK', 'Nama', 'TanggalLahir', 'Alamat']
    valid_fields = sum(1 for f in required_fields if parsed_fields.get(f))
    total_fields = len(required_fields)
    confidence = valid_fields / total_fields  # 0.0 - 1.0

    # --- Tentukan status ---
    if confidence == 1.0:
        return "Verified"
    elif confidence >= 0.75:
        return "Manual Review"
    else:
        return "Rejected"

from typing import Dict
import re

def parse_ktp(ocr_text: str) -> Dict[str, str]:
    fields = {
        "NIK": "",
        "Nama": "",
        "Tempat": "",
        "TanggalLahir": "",
        "JenisKelamin": "",
        "Alamat": "",
        "RT/RW": "",
        "Kel/Desa": "",
        "Kecamatan": "",
        "Agama": "",
        "StatusPerkawinan": "",
        "Pekerjaan": "",
        "Kewarganegaraan": "",
        "GolDarah": "",
        "BerlakuHingga": ""
    }

    text = " ".join(ocr_text.splitlines())

    # --- Basic fields ---
    nik = re.search(r"\b\d{16}\b", text)
    if nik: fields["NIK"] = nik.group(0)

    tgl_lahir = re.search(r"\b\d{2}-\d{2}-\d{4}\b", text)
    if tgl_lahir: fields["TanggalLahir"] = tgl_lahir.group(0)

    jk = re.search(r"\b(PEREMPUAN|LAKI-?LAKI)\b", text, re.IGNORECASE)
    if jk: fields["JenisKelamin"] = jk.group(0).capitalize()

    gol = re.search(r"Gol\.\s*Darah[:\s]*([A-ZABO]+)", text, re.IGNORECASE)
    if gol: fields["GolDarah"] = gol.group(1).upper()

    berlaku = re.search(r"BERLAKU HINGGA[:\s]*(\d{2}-\d{2}-\d{4})", text, re.IGNORECASE)
    if berlaku: 
        fields["BerlakuHingga"] = berlaku.group(1)
    else:
        # fallback ambil tanggal kedua
        dates = re.findall(r"\b\d{2}-\d{2}-\d{4}\b", text)
        if dates and len(dates) >= 2:
            fields["BerlakuHingga"] = dates[-2]

    kewarganegaraan = re.search(r"\b(WNI|WNA)\b", text, re.IGNORECASE)
    if kewarganegaraan: fields["Kewarganegaraan"] = kewarganegaraan.group(0).upper()

    status = re.search(r"\b(KAWIN|BELUM KAWIN|CERAI HIDUP|CERAI MATI)\b", text, re.IGNORECASE)
    if status: fields["StatusPerkawinan"] = status.group(0).title()

    agama = re.search(r"\b(ISLAM|KRISTEN|KATOLIK|HINDU|BUDDHA|KONGHUCU)\b", text, re.IGNORECASE)
    if agama: fields["Agama"] = agama.group(0).title()

    # --- Tempat lahir ---
    if fields["TanggalLahir"]:
        m = re.search(r"([A-Z][A-Z\s]+?),\s*" + re.escape(fields["TanggalLahir"]), text, re.IGNORECASE)
        if m: fields["Tempat"] = m.group(1).title()

    # --- Nama ---
    if fields["NIK"] and fields["Tempat"]:
        pattern = rf"{fields['NIK']}[:\s]*([A-Z][A-Z\s]+?)[:\s]*{fields['Tempat']}"
        m = re.search(pattern, text, re.IGNORECASE)
        if m: fields["Nama"] = m.group(1).title()

    # --- Alamat, RT/RW, Kel/Desa, Kecamatan ---
    lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]

    # cari index Jenis Kelamin
    try:
        idx_jk = next(i for i, l in enumerate(lines) if fields["JenisKelamin"].upper() in l.upper())
        # alamat biasanya baris berikutnya
        fields["Alamat"] = lines[idx_jk + 1].replace(":", "").strip()
        fields["RT/RW"] = lines[idx_jk + 2].replace(":", "").strip()
        fields["Kel/Desa"] = lines[idx_jk + 3].replace(":", "").strip()
        fields["Kecamatan"] = lines[idx_jk + 4].replace(":", "").strip()
    except Exception:
        pass

    # --- Pekerjaan ---
    if fields["Kewarganegaraan"] and fields["Agama"]:
        pattern = rf"{fields['Agama']}[:\s]*(.*?)\s+{fields['Kewarganegaraan']}"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            pekerjaan = m.group(1).replace(":", "").strip()
            fields["Pekerjaan"] = pekerjaan.title()

    # --- Cleanup ---
    for k in fields:
        fields[k] = fields[k].strip()

    return fields

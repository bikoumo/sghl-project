"""Génération PDF / Excel des dossiers et reçus."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from django.http import HttpResponse


def build_consultation_receipt_pdf(consultation, invoice=None) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    p.setFont('Helvetica-Bold', 16)
    p.drawString(50, y, 'SGHL — Reçu de consultation')
    y -= 28
    p.setFont('Helvetica', 11)
    p.drawString(50, y, f"Date : {consultation.date.strftime('%d/%m/%Y %H:%M')}")
    y -= 18
    p.drawString(50, y, f"Patient : {consultation.patient.get_full_name() or consultation.patient.username}")
    y -= 18
    p.drawString(50, y, f"Médecin : Dr {consultation.doctor.get_full_name() or consultation.doctor.username}")
    y -= 18
    if getattr(consultation.patient, 'matricule', None):
        p.drawString(50, y, f"Matricule : {consultation.patient.matricule}")
        y -= 18

    y -= 10
    p.setFont('Helvetica-Bold', 12)
    p.drawString(50, y, 'Compte rendu')
    y -= 20
    p.setFont('Helvetica', 10)

    def write_block(title, text):
        nonlocal y
        p.setFont('Helvetica-Bold', 10)
        p.drawString(50, y, title)
        y -= 14
        p.setFont('Helvetica', 10)
        for line in _wrap(text or '—', 90):
            if y < 80:
                p.showPage()
                y = height - 50
                p.setFont('Helvetica', 10)
            p.drawString(60, y, line)
            y -= 13
        y -= 8

    write_block('Symptômes', consultation.symptoms)
    write_block('Diagnostic', consultation.diagnosis)
    write_block('Prescription', consultation.prescription)

    if invoice:
        y -= 6
        p.setFont('Helvetica-Bold', 12)
        p.drawString(50, y, 'Facturation')
        y -= 18
        p.setFont('Helvetica', 10)
        p.drawString(50, y, f"Facture #{invoice.id} — {invoice.label}")
        y -= 14
        p.drawString(50, y, f"Montant : {invoice.total_amount} FCFA")
        y -= 14
        p.drawString(50, y, f"Statut : {invoice.status}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.read()


def build_patient_record_pdf(patient, consultations) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    p.setFont('Helvetica-Bold', 16)
    p.drawString(50, y, 'SGHL — Dossier médical')
    y -= 26
    p.setFont('Helvetica', 11)
    full_name = f"{patient.first_name} {patient.last_name}".strip() or patient.username
    p.drawString(50, y, f"Patient : {full_name}")
    y -= 16
    p.drawString(50, y, f"Matricule : {getattr(patient, 'matricule', None) or f'PT-{patient.id}'}")
    y -= 16
    p.drawString(50, y, f"Téléphone : {patient.phone or '—'}")
    y -= 16
    p.drawString(50, y, f"Naissance : {patient.birth_date or '—'}")
    y -= 16
    p.drawString(50, y, f"Groupe sanguin : {patient.groupe_sanguin or '—'}")
    y -= 16
    p.drawString(50, y, f"Allergies : {(patient.allergies or '—')[:90]}")
    y -= 28

    p.setFont('Helvetica-Bold', 12)
    p.drawString(50, y, 'Historique des consultations')
    y -= 20

    for c in consultations:
        if y < 120:
            p.showPage()
            y = height - 50
        p.setFont('Helvetica-Bold', 10)
        p.drawString(50, y, f"{c.date.strftime('%d/%m/%Y %H:%M')} — Dr {c.doctor.username}")
        y -= 14
        p.setFont('Helvetica', 10)
        for line in _wrap(f"Diagnostic : {c.diagnosis}", 95):
            p.drawString(60, y, line)
            y -= 12
        for line in _wrap(f"Symptômes : {c.symptoms}", 95):
            p.drawString(60, y, line)
            y -= 12
        if c.prescription:
            for line in _wrap(f"Prescription : {c.prescription}", 95):
                p.drawString(60, y, line)
                y -= 12
        y -= 10

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.read()


def build_patient_record_excel_response(patient, consultations) -> HttpResponse:
    try:
        from openpyxl import Workbook
    except ImportError:
        # Repli CSV nommé .xlsx si openpyxl absent (toujours utilisable)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="dossier_{patient.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Matricule', 'Nom', 'Prenom', 'Telephone', 'Naissance', 'Groupe sanguin'])
        writer.writerow([
            getattr(patient, 'matricule', '') or f'PT-{patient.id}',
            patient.last_name,
            patient.first_name,
            patient.phone or '',
            str(patient.birth_date or ''),
            patient.groupe_sanguin or '',
        ])
        writer.writerow([])
        writer.writerow(['Date', 'Medecin', 'Symptomes', 'Diagnostic', 'Prescription'])
        for c in consultations:
            writer.writerow([
                c.date.isoformat(),
                c.doctor.username,
                c.symptoms,
                c.diagnosis,
                c.prescription or '',
            ])
        return response

    wb = Workbook()
    info = wb.active
    info.title = 'Identite'
    info.append(['Champ', 'Valeur'])
    info.append(['Matricule', getattr(patient, 'matricule', None) or f'PT-{patient.id}'])
    info.append(['Nom', patient.last_name or ''])
    info.append(['Prénom', patient.first_name or ''])
    info.append(['Téléphone', patient.phone or ''])
    info.append(['Email', patient.email or ''])
    info.append(['Naissance', str(patient.birth_date or '')])
    info.append(['Genre', patient.gender or ''])
    info.append(['Groupe sanguin', patient.groupe_sanguin or ''])
    info.append(['Allergies', patient.allergies or ''])
    info.append(['Antécédents', patient.antecedents or ''])
    info.append(['Exporté le', datetime.now().isoformat(timespec='seconds')])

    hist = wb.create_sheet('Consultations')
    hist.append(['Date', 'Médecin', 'Symptômes', 'Diagnostic', 'Prescription'])
    for c in consultations:
        hist.append([
            c.date.isoformat(),
            c.doctor.username,
            c.symptoms,
            c.diagnosis,
            c.prescription or '',
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="dossier_{patient.id}.xlsx"'
    return response


def _wrap(text: str, width: int) -> list[str]:
    text = (text or '').replace('\n', ' ')
    words = text.split()
    if not words:
        return ['—']
    lines = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= width:
            current += ' ' + word
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

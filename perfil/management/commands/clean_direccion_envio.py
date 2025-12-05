from django.core.management.base import BaseCommand
import re

from home.models import UsuarioCliente, Pedido

def _clean_text(s: str) -> str:
    if not s:
        return ''

    cleaned = re.sub(r'\bNone\b', '', s)

    cleaned = re.sub(r',\s*,+', ',', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)

    cleaned = cleaned.strip()
    cleaned = re.sub(r'^[,\s]+|[,\s]+$', '', cleaned)

    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = cleaned.strip()
    return cleaned

class Command(BaseCommand):
    help = 'Limpia el campo direccion_envio de UsuarioCliente y Pedido eliminando literales "None" y zonas vacías.'

    def handle(self, *args, **options):
        uc_qs = UsuarioCliente.objects.filter(direccion_envio__icontains='None')
        affected_ids = list(uc_qs.values_list('id', flat=True))
        updated_uc = 0
        for uc in uc_qs:
            original = uc.direccion_envio or ''
            new = _clean_text(original)
            if new != original:
                uc.direccion_envio = new
                uc.save()
                updated_uc += 1

        pedido_qs = Pedido.objects.filter(direccion_envio__icontains='None')
        updated_pedido = 0
        for p in pedido_qs:
            original = p.direccion_envio or ''
            new = _clean_text(original)
            if new != original:
                p.direccion_envio = new
                p.save()
                updated_pedido += 1

        self.stdout.write(self.style.SUCCESS(f'UsuarioCliente actualizados: {updated_uc}'))
        self.stdout.write(self.style.SUCCESS(f'Pedidos actualizados: {updated_pedido}'))

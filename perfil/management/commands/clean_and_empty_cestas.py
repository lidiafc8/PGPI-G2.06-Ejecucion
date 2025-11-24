from django.core.management.base import BaseCommand
import re

from home.models import UsuarioCliente, Pedido, CestaCompra


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
    help = (
        'Limpia el campo direccion_envio de UsuarioCliente y Pedido eliminando literales "None" y zonas vacías, '
        'y vacía las cestas de compra asociadas a los usuarios afectados.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se haría sin modificar la base de datos')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # Esta utilidad vacía las cestas asociadas a UsuarioCliente cuyos campos de
        # `direccion_envio` contienen la cadena 'None'. No modifica direcciones.
        uc_qs = UsuarioCliente.objects.filter(direccion_envio__icontains='None')
        affected_ids = list(uc_qs.values_list('id', flat=True))

        count_cestas = CestaCompra.objects.filter(usuario_cliente_id__in=affected_ids).count() if affected_ids else 0

        self.stdout.write(self.style.WARNING('Resumen (previo a la acción):'))
        self.stdout.write(f'  UsuarioCliente afectados (con "None" en direccion_envio): {len(affected_ids)}')
        self.stdout.write(f'  Cestas asociadas a esos UsuarioCliente: {count_cestas}')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry-run activado; no se harán cambios.'))
            return

        # Vaciar cestas (borrar items) asociadas a UsuarioCliente afectados
        emptied_cestas = 0
        if affected_ids:
            cestas_qs = CestaCompra.objects.filter(usuario_cliente_id__in=affected_ids)
            for cesta in cestas_qs:
                cesta.items.all().delete()
                emptied_cestas += 1

        self.stdout.write(self.style.SUCCESS(f'Cestas vaciadas (items eliminados): {emptied_cestas}'))

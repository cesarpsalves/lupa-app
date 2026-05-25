"""Empresa (tenant) + presets de nicho + membership.

Empresa NÃO herda de TenantModel — ela É o tenant.
Membership liga User ↔ Company com um role.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.managers import AllObjectsManager
from apps.core.models import TimestampedModel


class ProfileLevel(models.TextChoices):
    L1 = "L1", _("Freelancer")
    L2 = "L2", _("Estúdio")
    L3 = "L3", _("Estúdio + Loja")


class Role(models.TextChoices):
    OWNER = "owner", _("Proprietário")
    MANAGER = "manager", _("Gerente")
    EMPLOYEE = "employee", _("Funcionário")
    VIEWER = "viewer", _("Visualizador")


class NichePreset(TimestampedModel):
    """Configuração por nicho: terminologia, serviços sugeridos, etc.

    Ativação controlada por flag `is_active` — só ativamos um nicho quando
    bate o threshold (15 interessados ou 50 pagantes do anterior).
    """

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    ticket_label = models.CharField(
        max_length=40,
        default="Atendimento",
        help_text="Como o nicho chama um 'atendimento'? (ex.: 'Ensaio', 'Sessão', 'OS')",
    )
    suggested_services = models.JSONField(
        default=list,
        help_text="Lista de objetos {name, base_price, duration_minutes}",
    )
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


def _company_logo_path(instance: Company, filename: str) -> str:
    return f"companies/{instance.slug}/logo/{filename}"


class Company(TimestampedModel):
    """Tenant. Toda informação operacional aponta pra cá via FK."""

    name = models.CharField(_("nome"), max_length=120)
    slug = models.SlugField(unique=True, max_length=140)
    document = models.CharField(_("CPF/CNPJ"), max_length=20, blank=True)
    niche = models.ForeignKey(NichePreset, on_delete=models.PROTECT, related_name="companies")
    profile_level = models.CharField(
        max_length=2,
        choices=ProfileLevel.choices,
        default=ProfileLevel.L1,
    )
    logo = models.ImageField(
        _("logo"),
        upload_to=_company_logo_path,
        blank=True,
        null=True,
        help_text="PNG/JPG, idealmente quadrado (≥ 256px). Opcional.",
    )
    settings = models.JSONField(
        default=dict,
        help_text="Configs flexíveis: default_signal_pct, working_hours, etc.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("empresa")
        verbose_name_plural = _("empresas")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base = slugify(self.name) or "empresa"
            slug = base
            suffix = 2
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{suffix}"
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def default_signal_pct(self) -> int:
        return int(self.settings.get("default_signal_pct", settings.LUPA_DEFAULT_SIGNAL_PCT))

    @property
    def initials(self) -> str:
        """Iniciais para avatar fallback. Máx 2 letras."""
        parts = [p for p in self.name.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def avatar_color(self) -> str:
        """Cor de fundo determinística baseada no slug (palette fixa)."""
        palette = [
            "#2c3d8c",  # lupa
            "#0f766e",  # teal
            "#9333ea",  # purple
            "#0891b2",  # cyan
            "#c2410c",  # orange
            "#65a30d",  # lime
            "#db2777",  # pink
            "#475569",  # slate
        ]
        import hashlib

        # MD5 aqui é só pra derivar uma cor visual a partir do slug — não é
        # uso criptográfico, então ignoramos o aviso do bandit.
        h = hashlib.md5(self.slug.encode(), usedforsecurity=False).hexdigest()
        return palette[int(h[:2], 16) % len(palette)]


class Membership(TimestampedModel):
    """User ↔ Company com role. Não usa TenantManager — admin/middleware
    precisam consultar antes de saber qual empresa está ativa."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="memberships",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    accepted_invitation = models.OneToOneField(
        "accounts.Invitation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membership",
    )

    all_objects = AllObjectsManager()
    # `objects` herda do Django padrão — Membership precisa ser consultável
    # antes do tenant estar resolvido (é como o tenant é resolvido!).
    objects = models.Manager()

    class Meta:
        unique_together = [("company", "user")]
        verbose_name = _("vínculo")
        verbose_name_plural = _("vínculos")

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.company.name} ({self.role})"

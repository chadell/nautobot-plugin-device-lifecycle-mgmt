"""Views implementation for the Lifecycle Management plugin."""
import base64
import io
import logging
import urllib

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

from django.db.models import Q, F, Count, ExpressionWrapper, FloatField

from nautobot.core.views import generic
from nautobot.dcim.models import Device
from nautobot.utilities.views import ContentTypePermissionRequiredMixin
from nautobot_device_lifecycle_mgmt import choices
from nautobot_device_lifecycle_mgmt.models import (
    HardwareLCM,
    SoftwareLCM,
    ContactLCM,
    ValidatedSoftwareLCM,
    DeviceSoftwareValidationResult,
    InventoryItemSoftwareValidationResult,
    ContractLCM,
    ProviderLCM,
)
from nautobot_device_lifecycle_mgmt.tables import (
    HardwareLCMTable,
    SoftwareLCMTable,
    ValidatedSoftwareLCMTable,
    ValidatedSoftwareDeviceReportTable,
    ValidatedSoftwareInventoryItemReportTable,
    ContractLCMTable,
    ProviderLCMTable,
    ContactLCMTable,
)
from nautobot_device_lifecycle_mgmt.forms import (
    HardwareLCMForm,
    HardwareLCMBulkEditForm,
    HardwareLCMFilterForm,
    HardwareLCMCSVForm,
    SoftwareLCMForm,
    SoftwareLCMFilterForm,
    SoftwareLCMCSVForm,
    ValidatedSoftwareLCMForm,
    ValidatedSoftwareLCMFilterForm,
    ValidatedSoftwareLCMCSVForm,
    ValidatedSoftwareDeviceReportFilterForm,
    ValidatedSoftwareInventoryItemReportFilterForm,
    ContractLCMForm,
    ContractLCMBulkEditForm,
    ContractLCMFilterForm,
    ContractLCMCSVForm,
    ProviderLCMForm,
    ProviderLCMBulkEditForm,
    ProviderLCMFilterForm,
    ProviderLCMCSVForm,
    ContactLCMForm,
    ContactLCMBulkEditForm,
    ContactLCMFilterForm,
    ContactLCMCSVForm,
)
from nautobot_device_lifecycle_mgmt.filters import (
    HardwareLCMFilterSet,
    ContractLCMFilterSet,
    ProviderLCMFilterSet,
    ContactLCMFilterSet,
    SoftwareLCMFilterSet,
    ValidatedSoftwareLCMFilterSet,
    ValidatedSoftwareDeviceReportFilterSet,
    ValidatedSoftwareInventoryItemReportFilterSet,
)

from nautobot_device_lifecycle_mgmt.const import URL, PLUGIN_CFG

logger = logging.getLogger("nautobot_device_lifecycle_mgmt")

# ---------------------------------------------------------------------------------
#  Hardware Lifecycle Management Views
# ---------------------------------------------------------------------------------
GREEN, RED, GREY = ("#D5E8D4", "#F8CECC", "#808080")


class HardwareLCMListView(generic.ObjectListView):
    """List view."""

    queryset = HardwareLCM.objects.prefetch_related("device_type")
    filterset = HardwareLCMFilterSet
    filterset_form = HardwareLCMFilterForm
    table = HardwareLCMTable


class HardwareLCMView(generic.ObjectView):
    """Detail view."""

    queryset = HardwareLCM.objects.prefetch_related("device_type")

    def get_extra_context(self, request, instance):
        """Return any additional context data for the template.

        request: The current request
        instance: The object being viewed
        """
        if instance.device_type:
            return {"devices": Device.objects.restrict(request.user, "view").filter(device_type=instance.device_type)}
        if instance.inventory_item:
            return {
                "devices": Device.objects.restrict(request.user, "view").filter(
                    inventoryitems__part_id=instance.inventory_item
                )
            }
        return {"devices": []}


class HardwareLCMCreateView(generic.ObjectEditView):
    """Create view."""

    model = HardwareLCM
    queryset = HardwareLCM.objects.prefetch_related("device_type")
    model_form = HardwareLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:hardwarelcm_list"


class HardwareLCMDeleteView(generic.ObjectDeleteView):
    """Delete view."""

    model = HardwareLCM
    queryset = HardwareLCM.objects.prefetch_related("device_type")
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:hardwarelcm_list"


class HardwareLCMEditView(generic.ObjectEditView):
    """Edit view."""

    model = HardwareLCM
    queryset = HardwareLCM.objects.prefetch_related("device_type")
    model_form = HardwareLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:hardwarelcm"


class HardwareLCMBulkImportView(generic.BulkImportView):
    """View for bulk import of hardware lcm."""

    queryset = HardwareLCM.objects.prefetch_related("device_type")
    model_form = HardwareLCMCSVForm
    table = HardwareLCMTable
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:hardwarelcm_list"


class HardwareLCMBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more HardwareLCM records."""

    queryset = HardwareLCM.objects.prefetch_related("device_type")
    table = HardwareLCMTable
    bulk_delete_url = "plugins:nautobot_device_lifecycle_mgmt.hardwarelcm_bulk_delete"
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:hardwarelcm_list"


class HardwareLCMBulkEditView(generic.BulkEditView):
    """View for editing one or more HardwareLCM records."""

    queryset = HardwareLCM.objects.prefetch_related("device_type")
    filterset = HardwareLCMFilterSet
    table = HardwareLCMTable
    form = HardwareLCMBulkEditForm
    bulk_edit_url = "plugins:nautobot_device_lifecycle_mgmt.hardwarelcm_bulk_edit"


class SoftwareLCMListView(generic.ObjectListView):
    """SoftwareLCM List view."""

    queryset = SoftwareLCM.objects.prefetch_related("device_platform")
    filterset = SoftwareLCMFilterSet
    filterset_form = SoftwareLCMFilterForm
    table = SoftwareLCMTable
    action_buttons = (
        "add",
        "delete",
        "import",
        "export",
    )
    template_name = "nautobot_device_lifecycle_mgmt/softwarelcm_list.html"


class SoftwareLCMView(generic.ObjectView):
    """SoftwareLCM Detail view."""

    queryset = SoftwareLCM.objects.prefetch_related("device_platform")


class SoftwareLCMCreateView(generic.ObjectEditView):
    """SoftwareLCM Create view."""

    model = SoftwareLCM
    queryset = SoftwareLCM.objects.prefetch_related("device_platform")
    model_form = SoftwareLCMForm
    default_return_url = URL.SoftwareLCM.List


class SoftwareLCMDeleteView(generic.ObjectDeleteView):
    """SoftwareLCM Delete view."""

    model = SoftwareLCM
    queryset = SoftwareLCM.objects.prefetch_related("device_platform")
    default_return_url = URL.SoftwareLCM.List
    template_name = "nautobot_device_lifecycle_mgmt/softwarelcm_delete.html"


class SoftwareLCMEditView(generic.ObjectEditView):
    """SoftwareLCM Edit view."""

    model = SoftwareLCM
    queryset = SoftwareLCM.objects.prefetch_related("device_platform")
    model_form = SoftwareLCMForm
    default_return_url = URL.SoftwareLCM.View


class SoftwareLCMBulkImportView(generic.BulkImportView):
    """View for bulk import of SoftwareLCM."""

    queryset = SoftwareLCM.objects.prefetch_related("device_platform")
    model_form = SoftwareLCMCSVForm
    table = SoftwareLCMTable
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:softwarelcm_list"


class ValidatedSoftwareLCMListView(generic.ObjectListView):
    """ValidatedSoftware List view."""

    queryset = ValidatedSoftwareLCM.objects.all()
    filterset = ValidatedSoftwareLCMFilterSet
    filterset_form = ValidatedSoftwareLCMFilterForm
    table = ValidatedSoftwareLCMTable
    action_buttons = (
        "add",
        "delete",
        "import",
        "export",
    )
    template_name = "nautobot_device_lifecycle_mgmt/validatedsoftwarelcm_list.html"


class ValidatedSoftwareLCMView(generic.ObjectView):
    """ValidatedSoftware Detail view."""

    queryset = ValidatedSoftwareLCM.objects.all()


class ValidatedSoftwareLCMEditView(generic.ObjectEditView):
    """ValidatedSoftware Create view."""

    queryset = ValidatedSoftwareLCM.objects.all()
    model_form = ValidatedSoftwareLCMForm
    template_name = "nautobot_device_lifecycle_mgmt/validatedsoftwarelcm_edit.html"
    default_return_url = URL.ValidatedSoftwareLCM.List


class ValidatedSoftwareLCMDeleteView(generic.ObjectDeleteView):
    """SoftwareLCM Delete view."""

    model = ValidatedSoftwareLCM
    queryset = ValidatedSoftwareLCM.objects.all()
    default_return_url = URL.ValidatedSoftwareLCM.List
    template_name = "nautobot_device_lifecycle_mgmt/validatedsoftwarelcm_delete.html"


class ValidatedSoftwareLCMBulkImportView(generic.BulkImportView):
    """View for bulk import of ValidatedSoftwareLCM."""

    queryset = ValidatedSoftwareLCM.objects.all()
    model_form = ValidatedSoftwareLCMCSVForm
    table = ValidatedSoftwareLCMTable
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:validatedsoftwarelcm_list"


class ReportOverviewHelper(ContentTypePermissionRequiredMixin, generic.View):
    """Customized overview view reports aggregation and filterset."""

    def get_required_permission(self):
        """Manually set permission when not tied to a model for global report."""
        return "nautobot_device_lifecycle_mgmt.view_validatedsoftwarelcm"

    @staticmethod
    def plot_piechart_visual(aggr, pie_chart_attrs):
        """Plot aggregation visual."""
        if aggr[pie_chart_attrs["aggr_labels"][0]] is None:
            return None
        sizes = [aggr[aggr_label] for aggr_label in pie_chart_attrs["aggr_labels"]]
        explode = (0.1, 0.1, 0.1)  # "explode" slices
        fig1, ax1 = plt.subplots()
        logging.debug(fig1)
        # labels = "Valid", "Invalid", "No Software"
        ax1.pie(
            sizes,
            explode=explode,
            labels=pie_chart_attrs["chart_labels"],
            autopct="%1.1f%%",
            colors=[GREEN, RED, GREY],
            shadow=True,
            startangle=90,
        )
        ax1.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title(aggr["name"], y=-0.1)
        fig = plt.gcf()
        # convert graph into string buffer and then we convert 64 bit code into image
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        string = base64.b64encode(buf.read())
        return urllib.parse.quote(string)

    @staticmethod
    def plot_barchart_visual(qs, chart_attrs):  # pylint: disable=too-many-locals
        """Construct report visual from queryset."""
        labels = [item[chart_attrs["label_accessor"]] for item in qs]

        label_locations = np.arange(len(labels))  # the label locations

        per_platform_bar_width = PLUGIN_CFG["per_platform_bar_width"]
        per_platform_width = PLUGIN_CFG["per_platform_width"]
        per_platform_height = PLUGIN_CFG["per_platform_height"]

        width = per_platform_bar_width  # the width of the bars

        fig, axis = plt.subplots(figsize=(per_platform_width, per_platform_height))

        rects = []
        for bar_pos, chart_bar in enumerate(chart_attrs["chart_bars"]):
            bar_label_item = [item[chart_bar["data_attr"]] for item in qs]
            rects.append(
                axis.bar(
                    label_locations - width + (bar_pos * width),
                    bar_label_item,
                    width,
                    label=chart_bar["label"],
                    color=chart_bar["color"],
                )
            )

        # Add some text for labels, title and custom x-axis tick labels, etc.
        axis.set_ylabel(chart_attrs["ylabel"])
        axis.set_title(chart_attrs["title"])
        axis.set_xticks(label_locations)
        axis.set_xticklabels(labels, rotation=0)
        # Force integer y-axis labels
        axis.yaxis.set_major_locator(MaxNLocator(integer=True))
        axis.margins(0.2, 0.2)
        axis.legend()

        def autolabel(rects):
            """Attach a text label above each bar in *rects*, displaying its height."""
            for rect in rects:
                height = rect.get_height()
                axis.annotate(
                    f"{height}",
                    xy=(rect.get_x() + rect.get_width() / 2, 0.5),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    rotation=90,
                )

        for rect in rects:
            autolabel(rect)

        # convert graph into dtring buffer and then we convert 64 bit code into image
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        string = base64.b64encode(buf.read())
        bar_chart = urllib.parse.quote(string)
        return bar_chart

    @staticmethod
    def calculate_aggr_percentage(aggr):
        """Calculate percentage of validated given aggregation fields.

        Returns:
            aggr: same aggr dict given as parameter with one new key
                - valid_percent
        """
        try:
            aggr["valid_percent"] = round(aggr["valid"] / aggr["total"] * 100, 2)
        except ZeroDivisionError:
            aggr["valid_percent"] = 0
        return aggr


class ValidatedSoftwareDeviceReportView(generic.ObjectListView):
    """View for executive report on software Validation."""

    filterset = ValidatedSoftwareDeviceReportFilterSet
    filterset_form = ValidatedSoftwareDeviceReportFilterForm
    table = ValidatedSoftwareDeviceReportTable
    template_name = "nautobot_device_lifecycle_mgmt/validatedsoftware_device_report.html"
    queryset = (
        DeviceSoftwareValidationResult.objects.values("device__device_type__model")
        .distinct()
        .annotate(
            total=Count("device__device_type__model"),
            valid=Count("device__device_type__model", filter=Q(is_validated=True)),
            invalid=Count("device__device_type__model", filter=Q(is_validated=False) and ~Q(software=None)),
            no_software=Count("device__device_type__model", filter=Q(software=None)),
            valid_percent=ExpressionWrapper(100 * F("valid") / (F("total")), output_field=FloatField()),
        )
        .order_by("-valid_percent")
    )

    # extra content dict to be returned by self.extra_context() method
    extra_content = {}

    def setup(self, request, *args, **kwargs):
        """Using request object to perform filtering based on query params."""
        super().setup(request, *args, **kwargs)  #
        try:
            report_last_run = (
                DeviceSoftwareValidationResult.objects.filter(run_type=choices.ReportRunTypeChoices.REPORT_FULL_RUN)
                .latest("last_updated")
                .last_run
            )
        except DeviceSoftwareValidationResult.DoesNotExist:
            report_last_run = None

        device_aggr = self.get_global_aggr(request)
        _platform_qs = (
            DeviceSoftwareValidationResult.objects.values("device__platform__name")
            .distinct()
            .annotate(
                total=Count("device__platform__name"),
                valid=Count("device__platform__name", filter=Q(is_validated=True)),
                invalid=Count("device__platform__name", filter=Q(is_validated=False) & ~Q(software=None)),
                no_software=Count("device__platform__name", filter=Q(software=None)),
            )
            .order_by("-total")
        )
        platform_qs = self.filterset(request.GET, _platform_qs).qs
        pie_chart_attrs = {
            "aggr_labels": ["valid", "invalid", "no_software"],
            "chart_labels": ["Valid", "Invalid", "No Software"],
        }
        bar_chart_attrs = {
            "label_accessor": "device__platform__name",
            "ylabel": "Device",
            "title": "Valid per Platform",
            "chart_bars": [
                {"label": "Valid", "data_attr": "valid", "color": GREEN},
                {"label": "Invalid", "data_attr": "invalid", "color": RED},
                {"label": "No Software", "data_attr": "no_software", "color": GREY},
            ],
        }
        self.extra_content = {
            "bar_chart": ReportOverviewHelper.plot_barchart_visual(platform_qs, bar_chart_attrs),
            "device_aggr": device_aggr,
            "device_visual": ReportOverviewHelper.plot_piechart_visual(device_aggr, pie_chart_attrs),
            "report_last_run": report_last_run,
        }

    def get_global_aggr(self, request):
        """Get device and inventory global reports.

        Returns:
            device_aggr: device global report dict
        """
        device_qs = DeviceSoftwareValidationResult.objects

        device_aggr = {}
        if self.filterset is not None:
            device_aggr = self.filterset(request.GET, device_qs).qs.aggregate(
                total=Count("device"),
                valid=Count("device", filter=Q(is_validated=True)),
                invalid=Count("device", filter=Q(is_validated=False) & ~Q(software=None)),
                no_software=Count("device", filter=Q(software=None)),
            )

            device_aggr["name"] = "Devices"

        return ReportOverviewHelper.calculate_aggr_percentage(device_aggr)

    def extra_context(self):
        """Extra content method on."""
        # add global aggregations to extra context.

        return self.extra_content


class ValidatedSoftwareInventoryItemReportView(generic.ObjectListView):
    """View for executive report on inventory item software validation."""

    filterset = ValidatedSoftwareInventoryItemReportFilterSet
    filterset_form = ValidatedSoftwareInventoryItemReportFilterForm
    table = ValidatedSoftwareInventoryItemReportTable
    template_name = "nautobot_device_lifecycle_mgmt/validatedsoftware_inventoryitem_report.html"
    queryset = (
        InventoryItemSoftwareValidationResult.objects.values("inventory_item__name")
        .distinct()
        .annotate(
            total=Count("inventory_item__name"),
            valid=Count("inventory_item__name", filter=Q(is_validated=True)),
            invalid=Count("inventory_item__name", filter=Q(is_validated=False) & ~Q(software=None)),
            no_software=Count("inventory_item__name", filter=Q(software=None)),
            valid_percent=ExpressionWrapper(100 * F("valid") / (F("total")), output_field=FloatField()),
        )
        .order_by("-valid_percent")
    )

    # extra content dict to be returned by self.extra_context() method
    extra_content = {}

    def setup(self, request, *args, **kwargs):
        """Using request object to perform filtering based on query params."""
        super().setup(request, *args, **kwargs)
        try:
            report_last_run = (
                InventoryItemSoftwareValidationResult.objects.filter(
                    run_type=choices.ReportRunTypeChoices.REPORT_FULL_RUN
                )
                .latest("last_updated")
                .last_run
            )
        except InventoryItemSoftwareValidationResult.DoesNotExist:
            report_last_run = None

        inventory_aggr = self.get_global_aggr(request)
        _platform_qs = (
            InventoryItemSoftwareValidationResult.objects.values("inventory_item__manufacturer__name")
            .distinct()
            .annotate(
                total=Count("inventory_item__manufacturer__name"),
                valid=Count("inventory_item__manufacturer__name", filter=Q(is_validated=True)),
                invalid=Count("inventory_item__manufacturer__name", filter=Q(is_validated=False) & ~Q(software=None)),
                no_software=Count("inventory_item__manufacturer__name", filter=Q(software=None)),
            )
            .order_by("-total")
        )
        platform_qs = self.filterset(request.GET, _platform_qs).qs

        pie_chart_attrs = {
            "aggr_labels": ["valid", "invalid", "no_software"],
            "chart_labels": ["Valid", "Invalid", "No Software"],
        }
        bar_chart_attrs = {
            "label_accessor": "inventory_item__manufacturer__name",
            "ylabel": "Inventory Item",
            "title": "Valid per Manufacturer",
            "chart_bars": [
                {"label": "Valid", "data_attr": "valid", "color": GREEN},
                {"label": "Invalid", "data_attr": "invalid", "color": RED},
                {"label": "No Software", "data_attr": "no_software", "color": GREY},
            ],
        }

        self.extra_content = {
            "bar_chart": ReportOverviewHelper.plot_barchart_visual(platform_qs, bar_chart_attrs),
            "inventory_aggr": inventory_aggr,
            "inventory_visual": ReportOverviewHelper.plot_piechart_visual(inventory_aggr, pie_chart_attrs),
            "report_last_run": report_last_run,
        }

    def get_global_aggr(self, request):
        """Get device and inventory global reports.

        Returns:
            inventory_aggr: inventory item global report dict
        """
        inventory_item_qs = InventoryItemSoftwareValidationResult.objects

        inventory_aggr = {}
        if self.filterset is not None:
            inventory_aggr = self.filterset(request.GET, inventory_item_qs).qs.aggregate(
                total=Count("inventory_item"),
                valid=Count("inventory_item", filter=Q(is_validated=True)),
                invalid=Count("inventory_item", filter=Q(is_validated=False) & ~Q(software=None)),
                no_software=Count("inventory_item", filter=Q(software=None)),
            )
            inventory_aggr["name"] = "Inventory Items"

        return ReportOverviewHelper.calculate_aggr_percentage(inventory_aggr)

    def extra_context(self):
        """Extra content method on."""
        # add global aggregations to extra context.

        return self.extra_content


# ---------------------------------------------------------------------------------
#  Contract Lifecycle Management Views
# ---------------------------------------------------------------------------------


class ContractLCMListView(generic.ObjectListView):
    """List view."""

    queryset = ContractLCM.objects.all()
    filterset = ContractLCMFilterSet
    filterset_form = ContractLCMFilterForm
    table = ContractLCMTable


class ContractLCMView(generic.ObjectView):
    """Detail view."""

    queryset = ContractLCM.objects.all()

    def get_extra_context(self, request, instance):
        """Return any additional context data for the template.

        request: The current request
        instance: The object being viewed
        """
        return {
            "contacts": ContactLCM.objects.restrict(request.user, "view")
            .filter(contract=instance)
            .exclude(type="Owner")
            .order_by("type", "priority"),
            "owners": ContactLCM.objects.restrict(request.user, "view")
            .filter(contract=instance, type="Owner")
            .order_by("type", "priority"),
        }


class ContractLCMCreateView(generic.ObjectEditView):
    """Create view."""

    model = ContractLCM
    queryset = ContractLCM.objects.all()
    model_form = ContractLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contractlcm_list"


class ContractLCMDeleteView(generic.ObjectDeleteView):
    """Delete view."""

    model = ContractLCM
    queryset = ContractLCM.objects.all()
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contractlcm_list"


class ContractLCMEditView(generic.ObjectEditView):
    """Edit view."""

    model = ContractLCM
    queryset = ContractLCM.objects.all()
    model_form = ContractLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contractlcm"


class ContractLCMBulkImportView(generic.BulkImportView):
    """View for bulk import of hardware lcm."""

    queryset = ContractLCM.objects.all()
    model_form = ContractLCMCSVForm
    table = ContractLCMTable
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contractlcm_list"


class ContractLCMBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more HardwareLCM records."""

    queryset = ContractLCM.objects.all()
    table = ContractLCMTable
    bulk_delete_url = "plugins:nautobot_device_lifecycle_mgmt.contractlcm_bulk_delete"
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contractlcm_list"


class ContractLCMBulkEditView(generic.BulkEditView):
    """View for editing one or more HardwareLCM records."""

    queryset = ContractLCM.objects.all()
    filterset = ContractLCMFilterSet
    table = ContractLCMTable
    form = ContractLCMBulkEditForm
    bulk_edit_url = "plugins:nautobot_device_lifecycle_mgmt.contractlcm_bulk_edit"


# ---------------------------------------------------------------------------------
#  Contract Provider Lifecycle Management Views
# ---------------------------------------------------------------------------------


class ProviderLCMListView(generic.ObjectListView):
    """List view."""

    queryset = ProviderLCM.objects.all()
    filterset = ProviderLCMFilterSet
    filterset_form = ProviderLCMFilterForm
    table = ProviderLCMTable


class ProviderLCMView(generic.ObjectView):
    """Detail view."""

    queryset = ProviderLCM.objects.all()

    def get_extra_context(self, request, instance):
        """Return any additional context data for the template.

        request: The current request
        instance: The object being viewed
        """
        return {"contracts": ContractLCM.objects.restrict(request.user, "view").filter(provider=instance)}


class ProviderLCMCreateView(generic.ObjectEditView):
    """Create view."""

    model = ProviderLCM
    queryset = ProviderLCM.objects.all()
    model_form = ProviderLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:providerlcm_list"


class ProviderLCMDeleteView(generic.ObjectDeleteView):
    """Delete view."""

    model = ProviderLCM
    queryset = ProviderLCM.objects.all()
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:providerlcm_list"


class ProviderLCMEditView(generic.ObjectEditView):
    """Edit view."""

    model = ProviderLCM
    queryset = ProviderLCM.objects.all()
    model_form = ProviderLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:providerlcm"


class ProviderLCMBulkImportView(generic.BulkImportView):
    """Bulk import view."""

    queryset = ProviderLCM.objects.all()
    model_form = ProviderLCMCSVForm
    table = ProviderLCMTable
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:providerlcm_list"


class ProviderLCMBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more HardwareLCM records."""

    queryset = ProviderLCM.objects.all()
    table = ProviderLCMTable
    bulk_delete_url = "plugins:nautobot_device_lifecycle_mgmt.providerlcm_bulk_delete"
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:providerlcm_list"


class ProviderLCMBulkEditView(generic.BulkEditView):
    """View for editing one or more HardwareLCM records."""

    queryset = ProviderLCM.objects.all()
    filterset = ProviderLCMFilterSet
    table = ProviderLCMTable
    form = ProviderLCMBulkEditForm
    bulk_edit_url = "plugins:nautobot_device_lifecycle_mgmt.providerlcm_bulk_edit"


# ---------------------------------------------------------------------------------
#  Contact POC Lifecycle Management Views
# ---------------------------------------------------------------------------------


class ContactLCMListView(generic.ObjectListView):
    """List view."""

    queryset = ContactLCM.objects.all()
    filterset = ContactLCMFilterSet
    filterset_form = ContactLCMFilterForm
    table = ContactLCMTable


class ContactLCMView(generic.ObjectView):
    """Detail view."""

    queryset = ContactLCM.objects.all()


class ContactLCMCreateView(generic.ObjectEditView):
    """Create view."""

    model = ContactLCM
    queryset = ContactLCM.objects.all()
    model_form = ContactLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contactlcm_list"


class ContactLCMDeleteView(generic.ObjectDeleteView):
    """Delete view."""

    model = ContactLCM
    queryset = ContactLCM.objects.all()
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contactlcm_list"


class ContactLCMEditView(generic.ObjectEditView):
    """Edit view."""

    model = ContactLCM
    queryset = ContactLCM.objects.all()
    model_form = ContactLCMForm
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contactlcm"


class ContactLCMBulkImportView(generic.BulkImportView):
    """Bulk import view."""

    queryset = ContactLCM.objects.all()
    model_form = ContactLCMCSVForm
    table = ContactLCMTable
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contactlcm_list"


class ContactLCMBulkDeleteView(generic.BulkDeleteView):
    """View for deleting one or more records."""

    queryset = ContactLCM.objects.all()
    table = ContactLCMTable
    bulk_delete_url = "plugins:nautobot_device_lifecycle_mgmt.contactlcm_bulk_delete"
    default_return_url = "plugins:nautobot_device_lifecycle_mgmt:contactlcm_list"


class ContactLCMBulkEditView(generic.BulkEditView):
    """View for editing one or more records."""

    queryset = ContactLCM.objects.all()
    filterset = ContactLCMFilterSet
    table = ContactLCMTable
    form = ContactLCMBulkEditForm
    bulk_edit_url = "plugins:nautobot_device_lifecycle_mgmt.contactlcm_bulk_edit"

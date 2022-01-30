from nautobot.dcim.choices import DeviceStatusChoices
from nautobot.dcim.models import ConsolePort, Device, PowerPort
from nautobot.extras.jobs import Job


class DeviceConnectionsReport(Job):
    description = "Validate the minimum physical connections for each device"

    def test_console_connection(self):

        # Check that every console port for every active device has a connection defined.
        active = DeviceStatusChoices.STATUS_ACTIVE
        for console_port in ConsolePort.objects.prefetch_related('device').filter(device__status=active):
            if console_port.connected_endpoint is None:
                self.log_failure(
                    obj=console_port.device,
                    message="No console connection defined for {}".format(console_port.name)
                )
            elif not console_port.connection_status:
                self.log_warning(
                    obj=console_port.device,
                    message="Console connection for {} marked as planned".format(console_port.name)
                )
            else:
                self.log_success(obj=console_port.device)

    def test_power_connections(self):

        # Check that every active device has at least two connected power supplies.
        for device in Device.objects.filter(status=DeviceStatusChoices.STATUS_ACTIVE):
            connected_ports = 0
            for power_port in PowerPort.objects.filter(device=device):
                if power_port.connected_endpoint is not None:
                    connected_ports += 1
                    if not power_port.connection_status:
                        self.log_warning(
                            obj=device,
                            message="Power connection for {} marked as planned".format(power_port.name)
                        )
            if connected_ports < 2:
                self.log_failure(
                    obj=device,
                    message="{} connected power supplies found (2 needed)".format(connected_ports)
                )
            else:
                self.log_success(obj=device)
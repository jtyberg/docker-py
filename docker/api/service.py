import six

from .. import errors
from .. import utils


class ServiceApiMixin(object):
    @utils.minimum_version('1.24')
    def services(self, filters=None):
        params = {
            'filters': utils.convert_filters(filters) if filters else None
        }
        url = self._url('/services')
        return self._result(self._get(url, params=params), True)

    @utils.minimum_version('1.24')
    def create_service(
            self, task_config, name=None, labels=None, mode=None,
            update_config=None, networks=None, endpoint_config=None
    ):
        url = self._url('/services/create')
        data = {
            'Name': name,
            'Labels': labels,
            'TaskTemplate': task_config,
            'Mode': mode,
            'UpdateConfig': update_config,
            'Networks': networks,
            'EndpointSpec': endpoint_config
        }
        return self._result(self._post_json(url, data=data), True)

    @utils.minimum_version('1.24')
    def inspect_service(self, service):
        url = self._url('/services/{0}', service)
        return self._result(self._get(url), True)

    @utils.minimum_version('1.24')
    def remove_service(self, service):
        url = self._url('/services/{0}', service)
        resp = self._delete(url)
        self._raise_for_status(resp)

    @utils.minimum_version('1.24')
    def tasks(self, filters=None):
        params = {
            'filters': utils.convert_filters(filters) if filters else None
        }
        url = self._url('/tasks')
        return self._result(self._get(url, params=params), True)

    @utils.minimum_version('1.24')
    def inspect_task(self, task):
        url = self._url('/tasks/{0}', task)
        return self._result(self._get(url), True)

class TaskConfig(dict):
    def __init__(self, container_spec, resources=None, restart_policy=None,
                 placement=None):
        self['ContainerSpec'] = container_spec
        if resources:
            self['Resources'] = resources
        if restart_policy:
            self['RestartPolicy'] = restart_policy
        if placement:
            self['Placement'] = placement

    @property
    def container_spec(self):
        return self.get('ContainerSpec')

    @property
    def resources(self):
        return self.get('Resources')

    @property
    def restart_policy(self):
        return self.get('RestartPolicy')

    @property
    def placement(self):
        return self.get('Placement')


class ContainerSpec(dict):
    def __init__(self, image, command=None, args=None, env=None, workdir=None,
                 user=None, labels=None, mounts=None, stop_grace_period=None):
        self['Image'] = image
        self['Command'] = command
        self['Args'] = args

        if env is not None:
            self['Env'] = env
        if workdir is not None:
            self['Dir'] = workdir
        if user is not None:
            self['User'] = user
        if labels is not None:
            self['Labels'] = labels
        if mounts is not None:
            for mount in mounts:
                if isinstance(mount, six.string_types):
                    mounts.append(Mount.parse_mount_string(mount))
                    mounts.remove(mount)
            self['Mounts'] = mounts
        if stop_grace_period is not None:
            self['StopGracePeriod'] = stop_grace_period


class Mount(dict):
    def __init__(self, target, source=None, type=None, populate=False,
                 propagation=None, mcs_access_mode=None, writable=True,
                 volume_driver=None):
        self['Target'] = target
        if source is not None:
            self['Source'] = source
        self['Type'] = type or 'bind'
        self['Populate'] = populate
        self['ReadOnly'] = not writable
        if propagation is not None:
            self['Propagation'] = propagation

        if mcs_access_mode is not None:
            self['MCSAccessMode'] = mcs_access_mode

        if volume_driver is not None:
            volume_options = {
                'DriverConfig': {
                    'Name': volume_driver
                }
            }
            self['VolumeOptions'] = volume_options

    @classmethod
    def parse_mount_string(cls, string):
        parts = string.split(',')
        mount = {}
        for part in parts:
            x = part.split('=')
            k,v = x[0], x[1]
            mount[k] = v
        writable = mount['writable'] if 'writable' in mount else 'rw'
        mount['writable'] = not (writable == 'ro')
        mount['volume_driver'] = mount.pop('volume-driver', None)
        target = mount.pop('target')
        return cls(target, **mount)

class Resources(dict):
    def __init__(self, cpu_limit=None, mem_limit=None, cpu_reservation=None,
                 mem_reservation=None):
        limits = {}
        reservation = {}
        if cpu_limit is not None:
            limits['CPU'] = cpu_limit
        if mem_limit is not None:
            limits['Memory'] = mem_limit
        if cpu_reservation is not None:
            reservation['CPU'] = cpu_reservation
        if mem_reservation is not None:
            reservation['Memory'] = mem_reservation

        self['Limits'] = limits
        self['Reservation'] = reservation


class RestartConditionTypesEnum(object):
    _values = (
        'none',
        'on_failure',
        'any',
    )
    NONE, ON_FAILURE, ANY = _values


class RestartPolicy(dict):
    condition_types = RestartConditionTypesEnum

    def __init__(self, condition=RestartConditionTypesEnum.NONE, delay=0,
                 attempts=0, window=0):
        if condition not in self.condition_types._values:
            raise TypeError(
                'Invalid RestartPolicy condition {0}'.format(condition)
            )

        self['Condition'] = condition
        self['Delay'] = delay
        self['Attempts'] = attempts
        self['Window'] = window

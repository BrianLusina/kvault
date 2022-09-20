import pickle
import os
from commands import BaseCommand
from ..exceptions import ClientQuit, Shutdown


class MiscCommands(BaseCommand):
    def _get_state(self):
        return {'kv': self._kv, 'schedule': self._schedule}

    def _set_state(self, state, merge=False):
        if not merge:
            self._kv = state['kv']
            self._schedule = state['schedule']
        else:
            def merge(orig, updates):
                orig.update(updates)
                return orig

            self._kv = merge(state['kv'], self._kv)
            self._schedule = state['schedule']

    def save_to_disk(self, filename):
        with open(filename, 'wb') as fh:
            pickle.dump(self._get_state(), fh, pickle.HIGHEST_PROTOCOL)
        return True

    def restore_from_disk(self, filename, merge=False):
        if not os.path.exists(filename):
            return False
        with open(filename, 'rb') as fh:
            state = pickle.load(fh)
        self._set_state(state, merge=merge)
        return True

    def merge_from_disk(self, filename):
        return self.restore_from_disk(filename, merge=True)

    def client_quit(self):
        raise ClientQuit('client closed connection')

    def shutdown(self):
        raise Shutdown('shutting down')

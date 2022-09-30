import heapq
import datetime
from .commands import BaseCommand
from ..utils import decode
from ..exceptions import CommandError


class ScheduleCommands(BaseCommand):
    def _decode_timestamp(self, timestamp):
        timestamp = decode(timestamp)
        fmt = '%Y-%m-%d %H:%M:%S'
        if '.' in timestamp:
            fmt = fmt + '.%f'
        try:
            return datetime.datetime.strptime(timestamp, fmt)
        except ValueError:
            raise CommandError('Timestamp must be formatted Y-m-d H:M:S')

    def schedule_add(self, timestamp, data):
        dt = self._decode_timestamp(timestamp)
        heapq.heappush(self._schedule, (dt, data))
        return 1

    def schedule_read(self, timestamp=None):
        dt = self._decode_timestamp(timestamp)
        accum = []
        while self._schedule and self._schedule[0][0] <= dt:
            ts, data = heapq.heappop(self._schedule)
            accum.append(data)
        return accum

    def schedule_flush(self):
        schedule_len = self.schedule_length()
        self._schedule = []
        return schedule_len

    def schedule_length(self):
        return len(self._schedule)

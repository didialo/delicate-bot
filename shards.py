import discord
from discord.ext import commands


class DelicateBot(commands.AutoShardedBot):

    def __init__(
        self,
        *,
        command_prefix="d!",
        intents: discord.Intents,
        help_command=None,
        **kwargs,
    ):
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            help_command=help_command,
            **kwargs,
        )

    def get_shard_latencies(self) -> list[tuple[int, int]]:
        """
        Return shard latency as:
        [(shard_id, latency_ms), ...]
        """

        return [
            (
                shard_id,
                max(
                    0,
                    round(latency * 1000),
                ),
            )
            for shard_id, latency in self.latencies
        ]

    def get_average_latency(self) -> int:
        """
        Return average latency across all active shards.
        """

        if not self.latencies:
            return 0

        total = sum(
            latency
            for _, latency in self.latencies
        )

        return max(
            0,
            round(
                (
                    total /
                    len(self.latencies)
                ) * 1000
            ),
        )

    def get_shard_count(self) -> int:
        """
        Return the number of active shards.
        """

        return len(
            self.shards
        )

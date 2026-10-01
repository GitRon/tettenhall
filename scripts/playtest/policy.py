from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class PlayerPolicy:
    """
    How the harness decides whether to march this month.

    A measuring stick, not an opponent: a policy settles the one choice the measurements so far have
    turned on, and everything else the player does is the same for every policy (see "PlayerTurn").
    """

    name: str
    # How many more men the band has to have than the target has on its feet. None marches regardless.
    margin: int | None

    def will_march(self, *, band_size: int, defenders: int) -> bool:
        return self.margin is None or band_size >= defenders + self.margin


POLICIES: dict[str, PlayerPolicy] = {
    policy.name: policy
    for policy in (
        PlayerPolicy(name="aggressive", margin=None),
        PlayerPolicy(name="even", margin=0),
        PlayerPolicy(name="prudent", margin=2),
    )
}

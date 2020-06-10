from CGRtools.containers import MoleculeContainer, ReactionContainer
from typing import Tuple
from .abc import ScrollABC
from .source import not_available


class Scroll(ScrollABC):
    @property
    def premolecules(self) -> Tuple['Scroll', ...]:
        in_scroll = list(self._synthons)
        target = in_scroll.pop(0)
        new_synthons_with_probs = zip(target.premolecules, target.probabilities)
        new_depth = self._depth + 1
        scrolls = []
        for pair in new_synthons_with_probs:
            synthons, probability = pair
            reaction = ReactionContainer(self._extract(synthons), [target.get_molecule])
            child_scroll = Scroll(in_scroll + self._filter(synthons), reaction, probability, new_depth)
            scrolls.append(child_scroll)
        return tuple(scrolls)

    @property
    def worse_value(self):
        return min([x.value for x in self._synthons])

    def _extract(self, synthons) -> Tuple[MoleculeContainer, ...]:
        return tuple([x.get_molecule for x in synthons])

    def _filter(self, synthons):
        comm_molecules = not_available([x.get_molecule for x in synthons])
        return [x for x in synthons if x.get_molecule in comm_molecules]


__all__ = ['Scroll']

from abc import abstractmethod
from collections import deque
from functools import cached_property
from pickle import load
from typing import Tuple, List, Generator, TYPE_CHECKING

from CGRtools import CGRReactor
from MorganFingerprint import MorganFingerprint
from torch import from_numpy
from torch.nn import BCELoss

from .abc import SynthonABC
from .source import not_available, SimpleNet, TwoHeadedNet

if TYPE_CHECKING:
    from numpy import array
    from CGRtools.containers import MoleculeContainer

morgan = MorganFingerprint(length=4096, min_radius=2, max_radius=4, number_bit_pairs=4)

net = TwoHeadedNet(module=SimpleNet,
                   criterion=BCELoss,
                   device='cpu',
                   module__int_size=4096,
                   module__out_size=2272,
                   module__hid_size=(2000,), )
net.initialize()
net.load_params(f_params='ThetaSynthesis/source/params/twohead_params.pkl')

with open('source files/rules_reverse.pickle', 'rb') as f:
    rules = load(f)
reactors = [CGRReactor(rule, delete_atoms=True) for rule in rules]


class Synthon(SynthonABC):
    @property
    def molecule(self) -> "MoleculeContainer":
        return self._molecule

    def premolecules(self, top_n: int = 5):
        for reactor in (reactors[idx] for idx, _ in self.__sorted_indices(top_n)):
            for mol in reactor(self.molecule):
                yield (type(self)(mol) for mol in mol.split())

    def probabilities(self, top_n: int = 5):
        return (prob for _, prob in self.__sorted_indices(top_n))

    @abstractmethod
    def value(self):
        ...

    def descriptor(self) -> "array":
        return from_numpy(morgan.transform([self.molecule])).float()

    def __sorted_indices(self, top_n: int):
        prediction = self.__neural_network()
        top_indices = prediction.argsort()[::-1][:top_n]
        return zip(top_indices, prediction[top_indices])

    def __neural_network(self) -> "array":
        return net.predict(self.descriptor().unsqueeze(0)).squeeze()


class CombineSynthon(Synthon):
    @cached_property
    def value(self):
        return self._neural_network[1].item()


class StupidSynthon(Synthon):
    @property
    def value(self):
        return 1


class SlowSynthon(StupidSynthon):
    @cached_property
    def value(self, roll_len: int = 10):
        """
        value get from rollout function
        """
        queue = deque([self])
        for _ in range(roll_len):
            reactant = queue.popleft()
            queue.extend(i for x in reactant.premolecules(1) for i in x)
            if not queue:
                return 1
        return 0


__all__ = ['Synthon', 'CombineSynthon', 'SlowSynthon', 'StupidSynthon']
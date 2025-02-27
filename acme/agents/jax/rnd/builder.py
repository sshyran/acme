# Copyright 2018 DeepMind Technologies Limited. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""RND Builder."""

from typing import Any, Callable, Iterator, List, Optional

from acme import adders
from acme import core
from acme import specs
from acme.agents.jax import builders
from acme.agents.jax.rnd import config as rnd_config
from acme.agents.jax.rnd import learning as rnd_learning
from acme.agents.jax.rnd import networks as rnd_networks
from acme.jax import networks as networks_lib
from acme.utils import counting
from acme.utils import loggers
import jax
import optax
import reverb


class RNDBuilder(builders.ActorLearnerBuilder):
  """RND Builder."""

  def __init__(
      self,
      rl_agent: builders.GenericActorLearnerBuilder,
      config: rnd_config.RNDConfig,
      logger_fn: Callable[[], loggers.Logger] = lambda: None,
  ):
    """Implements a builder for RND using rl_agent as forward RL algorithm.

    Args:
      rl_agent: The standard RL agent used by RND to optimize the generator.
      config: A config with RND HPs.
      logger_fn: a logger factory for the learner
    """
    self._rl_agent = rl_agent
    self._config = config
    self._logger_fn = logger_fn

  def make_learner(
      self,
      random_key: networks_lib.PRNGKey,
      networks: rnd_networks.RNDNetworks,
      dataset: Iterator[reverb.ReplaySample],
      replay_client: Optional[reverb.Client] = None,
      counter: Optional[counting.Counter] = None,
  ) -> core.Learner:
    direct_rl_learner_key, rnd_learner_key = jax.random.split(random_key)

    counter = counter or counting.Counter()
    direct_rl_counter = counting.Counter(counter, 'direct_rl')

    def direct_rl_learner_factory(
        networks: Any, dataset: Iterator[reverb.ReplaySample]) -> core.Learner:
      return self._rl_agent.make_learner(
          direct_rl_learner_key,
          networks,
          dataset,
          replay_client=replay_client,
          counter=direct_rl_counter)

    optimizer = optax.adam(learning_rate=self._config.predictor_learning_rate)

    return rnd_learning.RNDLearner(
        direct_rl_learner_factory=direct_rl_learner_factory,
        iterator=dataset,
        optimizer=optimizer,
        rnd_network=networks,
        rng_key=rnd_learner_key,
        is_sequence_based=self._config.is_sequence_based,
        grad_updates_per_batch=self._config.num_sgd_steps_per_step,
        counter=counter,
        logger=self._logger_fn())

  def make_replay_tables(
      self, environment_spec: specs.EnvironmentSpec) -> List[reverb.Table]:
    return self._rl_agent.make_replay_tables(environment_spec)

  def make_dataset_iterator(
      self,
      replay_client: reverb.Client) -> Optional[Iterator[reverb.ReplaySample]]:
    return self._rl_agent.make_dataset_iterator(replay_client)

  def make_adder(self,
                 replay_client: reverb.Client) -> Optional[adders.Adder]:
    return self._rl_agent.make_adder(replay_client)

  def make_actor(
      self,
      random_key: networks_lib.PRNGKey,
      policy_network,
      adder: Optional[adders.Adder] = None,
      variable_source: Optional[core.VariableSource] = None,
  ) -> core.Actor:
    return self._rl_agent.make_actor(random_key, policy_network, adder,
                                     variable_source)

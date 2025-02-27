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

"""OpenAI Gym environment factory."""

from typing import Mapping, Sequence

from acme import specs
from acme import types
from acme import wrappers
from acme.datasets import tfds
from acme.tf import networks
from acme.tf import utils as tf2_utils
import dm_env
import gym
import jax
import numpy as np
import sonnet as snt

TASKS = {
    'debug': ['MountainCarContinuous-v0'],
    'default': [
        'HalfCheetah-v2', 'Hopper-v2', 'InvertedDoublePendulum-v2',
        'InvertedPendulum-v2', 'Reacher-v2', 'Swimmer-v2', 'Walker2d-v2'
    ],
}


def make_environment(
    task: str = 'MountainCarContinuous-v0') -> dm_env.Environment:
  """Creates an OpenAI Gym environment."""

  # Load the gym environment.
  environment = gym.make(task)

  # Make sure the environment obeys the dm_env.Environment interface.
  environment = wrappers.GymWrapper(environment)
  # Clip the action returned by the agent to the environment spec.
  environment = wrappers.CanonicalSpecWrapper(environment, clip=True)
  environment = wrappers.SinglePrecisionWrapper(environment)

  return environment


def make_networks(
    action_spec: specs.BoundedArray,
    policy_layer_sizes: Sequence[int] = (256, 256, 256),
    critic_layer_sizes: Sequence[int] = (512, 512, 256),
    vmin: float = -150.,
    vmax: float = 150.,
    num_atoms: int = 51,
) -> Mapping[str, types.TensorTransformation]:
  """Creates networks used by the agent."""

  # Get total number of action dimensions from action spec.
  num_dimensions = np.prod(action_spec.shape, dtype=int)

  # Create the shared observation network; here simply a state-less operation.
  observation_network = tf2_utils.batch_concat

  # Create the policy network.
  policy_network = snt.Sequential([
      networks.LayerNormMLP(policy_layer_sizes, activate_final=True),
      networks.NearZeroInitializedLinear(num_dimensions),
      networks.TanhToSpec(action_spec),
  ])

  # Create the critic network.
  critic_network = snt.Sequential([
      # The multiplexer concatenates the observations/actions.
      networks.CriticMultiplexer(),
      networks.LayerNormMLP(critic_layer_sizes, activate_final=True),
      networks.DiscreteValuedHead(vmin, vmax, num_atoms),
  ])

  return {
      'policy': policy_network,
      'critic': critic_network,
      'observation': observation_network,
  }


def make_demonstration_iterator(batch_size: int,
                                dataset_name: str,
                                seed: int = 0):
  dataset = tfds.get_tfds_dataset(dataset_name)
  return tfds.JaxInMemoryRandomSampleIterator(dataset, jax.random.PRNGKey(seed),
                                              batch_size)

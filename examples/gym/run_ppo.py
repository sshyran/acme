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

"""Example running PPO on the OpenAI Gym.

Runs the synchronous PPO agent.
"""

from absl import flags
from acme import specs
from acme.agents.jax import ppo
from absl import app
import helpers
from acme.jax import runners
from acme.utils import experiment_utils

FLAGS = flags.FLAGS
flags.DEFINE_integer('num_steps', 4000000,
                     'Number of env steps to run training for.')
flags.DEFINE_integer('eval_every', 10000, 'How often to run evaluation')
flags.DEFINE_string('env_name', 'MountainCarContinuous-v0',
                    'What environment to run')

# PPO agent configuration flags.
flags.DEFINE_integer('unroll_length', 16, 'Unroll length.')
flags.DEFINE_integer('num_minibatches', 32, 'Number of minibatches.')
flags.DEFINE_integer('num_epochs', 10, 'Number of epochs.')
flags.DEFINE_integer('batch_size', 2048 // 16, 'Batch size.')

flags.DEFINE_integer('seed', 0, 'Random seed.')


def main(_):
  # Create an environment, grab the spec, and use it to create networks.
  environment = helpers.make_environment(task=FLAGS.env_name)
  environment_spec = specs.make_environment_spec(environment)
  agent_networks = ppo.make_continuous_networks(environment_spec)

  # Construct the agent.
  config = ppo.PPOConfig(
      unroll_length=FLAGS.unroll_length,
      num_minibatches=FLAGS.num_minibatches,
      num_epochs=FLAGS.num_epochs,
      batch_size=FLAGS.batch_size)

  learner_logger = experiment_utils.make_experiment_logger(
      label='learner', steps_key='learner_steps')

  ppo_builder = ppo.PPOBuilder(config, logger_fn=(lambda: learner_logger))

  runners.run_agent(
      builder=ppo_builder,
      environment=environment,
      num_steps=FLAGS.num_steps,
      eval_every=FLAGS.eval_every,
      seed=FLAGS.seed,
      networks=agent_networks,
      policy_network=ppo.make_inference_fn(agent_networks),
      eval_policy_network=ppo.make_inference_fn(
          agent_networks, evaluation=True))


if __name__ == '__main__':
  app.run(main)

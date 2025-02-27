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

"""Importance-weighted actor-learner architecture (IMPALA) agent."""
# pylint: disable=g-bad-import-order

from acme.agents.jax.impala.agent import IMPALA
from acme.agents.jax.impala.agent import IMPALAFromConfig
from acme.agents.jax.impala.config import IMPALAConfig
from acme.agents.jax.impala.learning import IMPALALearner
from acme.agents.jax.impala.networks import IMPALANetworks
from acme.agents.jax.impala.networks import make_atari_networks
from acme.agents.jax.impala.networks import make_haiku_networks

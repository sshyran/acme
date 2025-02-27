#!/bin/bash
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


# Bash settings: fail on any error and display all commands being run.
set -e
set -x

# Python must be 3.7 or higher.
python --version

# Set up a virtual environment.
python -m venv acme_testing
source acme_testing/bin/activate

# Install dependencies.
pip install --upgrade pip setuptools wheel xmanager
pip install .[jax,tf,launchpad,testing,envs]


N_CPU=$(grep -c ^processor /proc/cpuinfo)
EXAMPLES=$(find examples/ -mindepth 1 -type d -not -path examples/offline -not -path examples/open_spiel)

# Run static type-checking.
for TESTDIR in acme ${EXAMPLES}; do
  pytype -k -j "${N_CPU}" "${TESTDIR}"
done

# Run all tests.
pytest --ignore-glob="*/*agent*_test.py" --durations=10 -n "${N_CPU}" acme

# Run sample of examples.
# For each of them make sure StepsLimiter reached the limit step count.
cd examples/gym
time python lp_ppo_jax.py --lp_termination_notice_secs=1 > /tmp/log.txt 2>&1 || cat /tmp/log.txt
cat /tmp/log.txt | grep -E 'StepsLimiter: Max steps of [0-9]+ was reached, terminating'
#time python lp_sac_jax.py --lp_termination_notice_secs=1 > /tmp/log.txt 2>&1 || cat /tmp/log.txt
#cat /tmp/log.txt | grep -E 'StepsLimiter: Max steps of [0-9]+ was reached, terminating'

# Run tests for non-distributed examples:
TEST_COUNT=0
for TEST in run_*.py; do
  if [[ "{$TEST}" =~ (run_ail|run_dac|run_gail|run_pwil|run_sqil|run_value_dice) ]]; then
    continue
  fi

  echo "TEST: ${TEST}"
  TEST_COUNT=$(($TEST_COUNT+1))
  time python "${TEST}" --num_steps=1000 --eval_every=1000
done
# Make sure number of executed examples is expected. This makes sure
# we will not forget to update this code when examples are renamed for example.
if [ $TEST_COUNT -ne 4 ]; then
  exit 1
fi

# Clean-up.
deactivate
ls -l
rm -rf acme_testing/

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest import mock

from deepdiff import DeepDiff

from server.routes.experiments.biomed_nl.entity_recognition import \
    annotate_query_with_types
from server.routes.experiments.biomed_nl.entity_recognition import \
    recognize_entities_from_query
from server.routes.experiments.biomed_nl.entity_recognition import \
    sample_dcids_by_type
from server.routes.experiments.biomed_nl.utils import GraphEntity


class TestRecognizeEntities(unittest.TestCase):

  def setUp(self):
    self.fetch_types_response = {
        'dc/1': [
            {
                'dcid': 'dc/typeA',
                'name': 'TypeA',
                'types': ['Class'],
            },
            {
                'dcid': 'dc/typeB',
                'name': 'TypeB',
                'types': ['Class'],
            },
        ],
        'dc/2': [{
            'dcid': 'dc/typeB',
            'name': 'TypeB',
            'types': ['Class'],
        },],
        'dc/3': [
            {
                'dcid': 'dc/typeB',
                'name': 'TypeB',
                'types': ['Class'],
            },
            {
                'dcid': 'dc/typeC',
                'name': 'TypeC',
                'types': ['Class'],
            },
        ],
    }

    self.fetch_types_side_effect = lambda dcids, _: {
        key: self.fetch_types_response[key] for key in dcids
    }

    self.v1_recognize_entities_response = [{
        "span": "entity1",
        "entities": [{
            "dcid": "dc/1"
        }]
    }, {
        "span": "second entity",
        "entities": [{
            "dcid": "dc/2"
        }, {
            "dcid": "dc/3"
        }]
    }]

  @mock.patch('server.lib.fetch.raw_property_values')
  def test_sample_dcids_adds_all_unique_types_exceeding_sample_size(
      self, mock_fetch):
    input_dcids = ['dc/1', 'dc/2', 'dc/3']

    mock_fetch.side_effect = [self.fetch_types_response]

    entities = sample_dcids_by_type("entity", input_dcids, 1)

    mock_fetch.assert_called_once_with(input_dcids, 'typeOf')
    assert entities == [
        GraphEntity(name="entity", dcid="dc/1", types=["TypeA", "TypeB"]),
        GraphEntity(name="entity", dcid="dc/3", types=["TypeB", "TypeC"])
    ]

  @mock.patch('server.lib.fetch.raw_property_values')
  def test_sample_dcids_adds_skipped_dcids_from_first_pass(self, mock_fetch):
    input_dcids = ['dc/1', 'dc/2', 'dc/3']

    mock_fetch.side_effect = self.fetch_types_side_effect

    entities = sample_dcids_by_type("entity", input_dcids, 3)

    mock_fetch.assert_called_once_with(input_dcids, 'typeOf')
    assert entities == [
        GraphEntity(name="entity", dcid="dc/1", types=["TypeA", "TypeB"]),
        GraphEntity(name="entity", dcid="dc/3", types=["TypeB", "TypeC"]),
        GraphEntity(name="entity", dcid="dc/2", types=["TypeB"]),
    ]

  @mock.patch('server.lib.fetch.raw_property_values')
  @mock.patch('server.services.datacommons.recognize_entities')
  def test_recognize_entities(self, mock_recognize, mock_fetch_types):

    mock_recognize.side_effect = [self.v1_recognize_entities_response]
    mock_fetch_types.side_effect = self.fetch_types_side_effect

    query = "query containing entity1 and second entity"
    entities = recognize_entities_from_query(query)

    mock_recognize.assert_called_once_with(query)
    mock_fetch_types.assert_has_calls(
        [mock.call(['dc/1'], 'typeOf'),
         mock.call(['dc/2', 'dc/3'], 'typeOf')])

    assert entities == [
        GraphEntity(name="entity1", dcid="dc/1", types=["TypeA", "TypeB"]),
        GraphEntity(name="second entity", dcid="dc/2", types=["TypeB"]),
        GraphEntity(name="second entity", dcid="dc/3", types=["TypeB", "TypeC"])
    ]

  def test_annotate_query_with_types(self):
    query = "query containing entity1 and second entity"
    entities_to_types = {
        'entity1': ['TypeA', 'TypeB'],
        'second entity': ['TypeB', 'TypeC']
    }
    assert annotate_query_with_types(
        query, entities_to_types
    ) == "query containing [entity1 (typeOf: TypeA, TypeB)] and [second entity (typeOf: TypeB, TypeC)]"

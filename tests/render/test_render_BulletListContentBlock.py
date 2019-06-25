from great_expectations.render.renderer.content_block import BulletListContentBlock

import glob
import json


def test_all_expectations_using_test_definitions():
    # Fetch test_definitions for all expectations.
    # Note: as of 6/20/2019, coverage is good, but not 100%
    test_files = glob.glob(
        "tests/test_definitions/*/expect*.json"
    )

    all_true = True
    failure_count, total_count = 0, 0
    types = []
    # Loop over all test_files, datasets, and tests:
    for filename in test_files:
        test_definitions = json.load(open(filename))
        types.append(test_definitions["expectation_type"])

        for dataset in test_definitions["datasets"]:

            for test in dataset["tests"]:
                # Construct an expectation from the test.
                if type(test["in"]) == dict:
                    fake_expectation = {
                        "expectation_type": test_definitions["expectation_type"],
                        "kwargs": test["in"],
                    }
                else:
                    # This would be a good place to put a kwarg-to-arg converter
                    continue

                try:
                    # Attempt to render it
                    render_result = BulletListContentBlock.render(
                        fake_expectation)
                    # print(fake_expectation)

                    # Assert that the rendered result matches the intended format.
                    # Note: THIS DOES NOT TEST CONTENT AT ALL.
                    # Abe 6/22/2019: For the moment, I think it's fine to not test content.
                    # I'm on the fence about the right end state for testing renderers at this level.
                    # Spot checks, perhaps?
                    assert render_result != None
                    assert type(render_result) == list
                    for el in render_result:
                        assert set(el.keys()) == {
                            'template', 'params'}

                except AssertionError:
                    # If the assertions fail, then print the expectation to allow debugging.
                    # Do NOT trap other errors, so that developers can debug using the full traceback.
                    print(fake_expectation)
                    all_true = False
                    failure_count += 1

                except Exception as e:
                    print(fake_expectation)
                    raise(e)

                total_count += 1

    # print(len(types))
    # print(len(set(types)))
    print(total_count-failure_count, "of", total_count,
          "suceeded (", 1-failure_count*1./total_count, ")")

    assert all_true

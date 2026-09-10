from apps.warband.training.forms import TrainingForm, build_training_category_help_text


def test_build_training_category_help_text_names_the_attribute_of_every_category():
    """
    "Weapon mastery", "Swiftness" and "Shield wall" name no attribute between them, and the overview
    they are chosen against has columns called Strength, Dexterity, Health and Morale.
    """
    assert build_training_category_help_text() == (
        "Weapon mastery grows Strength or Morale. Swiftness grows Dexterity. Shield wall grows Health or Morale."
    )


def test_training_form_carries_the_category_help_text():
    form = TrainingForm()

    assert form.fields["category"].help_text == build_training_category_help_text()

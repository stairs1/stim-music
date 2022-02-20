/*
  ==============================================================================

    This file contains the basic framework code for a JUCE plugin editor.

  ==============================================================================
*/

#include "PluginProcessor.h"
#include "PluginEditor.h"

//==============================================================================
FirstVSTAudioProcessorEditor::FirstVSTAudioProcessorEditor (FirstVSTAudioProcessor& p)
    : AudioProcessorEditor (&p), audioProcessor (p)
{
    // Make sure that before the constructor has finished, you've set the
    // editor's size to whatever you need it to be.
    setSize (400, 300);
    
    // these define the parameters of our slider object <<>>
    midiVolume.setSliderStyle (juce::Slider::LinearBarVertical);
    midiVolume.setRange (0.0, 127.0, 1.0);
    midiVolume.setTextBoxStyle (juce::Slider::NoTextBox, false, 90, 0);
    midiVolume.setPopupDisplayEnabled (true, false, this);
    midiVolume.setTextValueSuffix (" Volume");
    midiVolume.setValue(1.0);
    
    // this function adds the slider to the editor <<>>
    addAndMakeVisible (&midiVolume);
    
    // add the listener to the slider
    midiVolume.addListener (this); // <<>>
}

FirstVSTAudioProcessorEditor::~FirstVSTAudioProcessorEditor()
{
}

void FirstVSTAudioProcessorEditor::sliderValueChanged (juce::Slider* slider)
{
    audioProcessor.noteOnVel = midiVolume.getValue();
}

//==============================================================================
void FirstVSTAudioProcessorEditor::paint (juce::Graphics& g)
{
    // (Our component is opaque, so we must completely fill the background with a solid colour)
    g.fillAll (getLookAndFeel().findColour (juce::ResizableWindow::backgroundColourId));

    g.setColour (juce::Colours::white);
    g.setFont (15.0f);
    g.drawFittedText ("CHECK DOUBLE CALL (actual)", getLocalBounds(), juce::Justification::centred, 1);
}

void FirstVSTAudioProcessorEditor::resized()
{
    // This is generally where you'll want to lay out the positions of any
    // subcomponents in your editor..
    
    // sets the position and size of the slider with arguments (x, y, width, height) <<>>
    midiVolume.setBounds (40, 30, 20, getHeight() - 60);
}

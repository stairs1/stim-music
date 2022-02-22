/*
  ==============================================================================

    This file contains the basic framework code for a JUCE plugin processor.

  ==============================================================================
*/

#include "PluginProcessor.h"
#include "PluginEditor.h"
//#include<std.h>
using namespace std;
//#include<thread>;
#include <pthread.h>
#include <unistd.h>
#include <cassert>


//==============================================================================
FirstVSTAudioProcessor::FirstVSTAudioProcessor()
#ifndef JucePlugin_PreferredChannelConfigurations
     : AudioProcessor (BusesProperties()
                     #if ! JucePlugin_IsMidiEffect
                      #if ! JucePlugin_IsSynth
                       .withInput  ("Input",  juce::AudioChannelSet::stereo(), true)
                      #endif
                       .withOutput ("Output", juce::AudioChannelSet::stereo(), true)
                     #endif
                       )
#endif
{
}

// Socket connection variables
//int sock;
//struct sockaddr_in server;
//char message[1000] , server_reply[2000];



FirstVSTAudioProcessor::~FirstVSTAudioProcessor()
{
}


//==============================================================================
const juce::String FirstVSTAudioProcessor::getName() const
{
    return JucePlugin_Name;
}

bool FirstVSTAudioProcessor::acceptsMidi() const
{
   #if JucePlugin_WantsMidiInput
    return true;
   #else
    return false;
   #endif
}

bool FirstVSTAudioProcessor::producesMidi() const
{
   #if JucePlugin_ProducesMidiOutput
    return true;
   #else
    return false;
   #endif
}

bool FirstVSTAudioProcessor::isMidiEffect() const
{
   #if JucePlugin_IsMidiEffect
    return true;
   #else
    return false;
   #endif
}

double FirstVSTAudioProcessor::getTailLengthSeconds() const
{
    return 0.0;
}

int FirstVSTAudioProcessor::getNumPrograms()
{
    return 1;   // NB: some hosts don't cope very well if you tell them there are 0 programs,
                // so this should be at least 1, even if you're not really implementing programs.
}

int FirstVSTAudioProcessor::getCurrentProgram()
{
    return 0;
}

void FirstVSTAudioProcessor::setCurrentProgram (int index)
{
}

const juce::String FirstVSTAudioProcessor::getProgramName (int index)
{
    return {};
}

void FirstVSTAudioProcessor::changeProgramName (int index, const juce::String& newName)
{
}

//==============================================================================
//volatile int set_me = 1;
atomic_int set_me(1);
int memory_trace = 0;

//void sendToCivilization(juce::StreamingSocket *srv, int& sm, int& mt) {
//    // Server, info, tcp connection...
//    std::string message = " lelele";
//    char const *c = message.c_str();
//    int cnte = 0;
//
//    if(true){
//        if(sm != mt) {
//            mt++;
//
//            cnte = srv->waitUntilReady(false, 500);
//            assert(cnte==1);
//            cnte = srv->write(c, (int)message.length());
//            assert(cnte != -1 && cnte != 0);
//        }
//    }
//    return;
//}

void* sendToCivilization(void* sv) {
    juce::StreamingSocket* srv = (juce::StreamingSocket*) sv;
    // Server, info, tcp connection...
    std::string message = "breh\n";
    std::string message2 = "breh ";
    char c[message2.length()+5];
    volatile int cnte = 0;

    // char const *con = message.c_str();

    while(true){
        if(memory_trace < set_me) {
            memory_trace++;

            message2 = message + to_string(memory_trace);

            for (int i = 0; i < message2.length(); i++) {
                c[i] = message2[i];
            }

            cnte = srv->waitUntilReady(false, 10);
            assert(cnte==1);
            cnte = srv->write(c, (int)message2.length());
            assert(cnte != -1);
            sleep(0.001);
        }
    }
    pthread_exit(0);
}


int hasRunPrepPlay = 0;

void FirstVSTAudioProcessor::prepareToPlay (double sampleRate, int samplesPerBlock)
{
    // Use this method as the place to do any pre-playback
    // initialisation that you need..

    // Check if this has run yet
//    if(hasRunPrepPlay == 0){
//
//
//
//    }

//    assert(hasRunPrepPlay == 0);
    if (hasRunPrepPlay == 1) {
        return;
    }

    int sock = 0;

    socket = new juce::StreamingSocket;
//    socket->bindToPort( 8889, "127.0.0.1" );

    sock = socket->connect("127.0.0.1", 8889);

    assert(sock);

    sock = socket->waitUntilReady(false, 5000);
    assert(sock==1);

    std::string message = "BRUHhhh\n";
    char const *c = message.c_str();
    sock = socket->write(c, (int)message.length());
    assert(sock != -1 && sock != 0);

    cnt = 0;// counter for various things.

//    nonWriteBuffer = new juce::AudioBuffer<float>(getTotalNumInputChannels(), getTotalNumOutputChannels());


    // (getTotalNumInputChannels(), getTotalNumOutputChannels());
//    sendToCivilization(socket);
    // TODO: Add worker thread initialization
    // sendToCivilization(3);
//    std::thread breh(sendToCivilization, socket, set_me, memory_trace);

    pthread_t threads[1];
    pthread_create (&threads[0], NULL, &sendToCivilization, (void *)socket);

    hasRunPrepPlay = 1;
}

void FirstVSTAudioProcessor::releaseResources()
{
    // When playback stops, you can use this as an opportunity to free up any
    // spare memory, etc.
}

#ifndef JucePlugin_PreferredChannelConfigurations
bool FirstVSTAudioProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
  #if JucePlugin_IsMidiEffect
    juce::ignoreUnused (layouts);
    return true;
  #else
    // This is the place where you check if the layout is supported.
    // In this template code we only support mono or stereo.
    // Some plugin hosts, such as certain GarageBand versions, will only
    // load plugins that support stereo bus layouts.
    if (layouts.getMainOutputChannelSet() != juce::AudioChannelSet::mono()
     && layouts.getMainOutputChannelSet() != juce::AudioChannelSet::stereo())
        return false;

    // This checks if the input layout matches the output layout
   #if ! JucePlugin_IsSynth
    if (layouts.getMainOutputChannelSet() != layouts.getMainInputChannelSet())
        return false;
   #endif

    return true;
  #endif
}
#endif


//std::atomic<int> set_me = 0; // updated by the main thread.
//std::atomic<int> memory_trace = 0; // updated by the worker thread; should be equal to set_me; if not, send "bruh".





void FirstVSTAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages)
{
    juce::ScopedNoDenormals noDenormals;
//    auto totalNumInputChannels  = getTotalNumInputChannels();
//    auto totalNumOutputChannels = getTotalNumOutputChannels();
//    auto numSamples = buffer.getNumSamples();

    // In case we have more outputs than inputs, this code clears any output
    // channels that didn't contain input data, (because these aren't
    // guaranteed to be empty - they may contain garbage).
    // This is here to avoid people getting screaming feedback
    // when they first compile a plugin, but obviously you don't need to keep
    // this code if your algorithm always overwrites all the output channels.

    /*
    for (auto i = totalNumInputChannels; i < totalNumOutputChannels; ++i)
        buffer.clear (i, 0, buffer.getNumSamples());
     */

    // This is the place where you'd normally do the guts of your plugin's
    // audio processing...
    // Make sure to reset the state if your inner loop is processing
    // the samples and the outer loop is handling the channels.
    // Alternatively, you can process the samples with the channels
    // interleaved by keeping the same state.

    /*
    float sum = 0;

    for (int channel = 0; channel < totalNumInputChannels; ++channel)
    {
        auto* channelData = buffer.getWritePointer (channel);
        for(int i = 0; i < numSamples; i++) {
            channelData[i] = channelData[i]*noteOnVel/128.0;
            sum += channelData[i]/numSamples;
        }
        // ..do something to the data...
    }

//    puts(std::to_string(sum));

    if(sum > 0) {
//        std::string message = "BRUHhhh";
//        char const *c = message.c_str();
//        cnt = socket->waitUntilReady(false, 1);
//        assert(cnt==1);
//        cnt = socket->write(c, (int)message.length());
//        assert(cnt != -1 && cnt != 0);
//        set_me++;
    }
     */

    // buffer.clear();


//    juce::MidiBuffer processedMidi;

    for (const auto metadata : midiMessages)
    {
        auto message = metadata.getMessage();
//        const auto time = metadata.samplePosition;

        if (message.isNoteOn())
        {

//            message = juce::MidiMessage::noteOn (message.getChannel(),
//                                                 message.getNoteNumber(),
//                                                 (juce::uint8) noteOnVel);
            set_me++;
//            assert(0);
        }

//        processedMidi.addEvent (message, time);
    }

//    midiMessages.swapWith (processedMidi);
}

//==============================================================================
bool FirstVSTAudioProcessor::hasEditor() const
{
    return true; // (change this to false if you choose to not supply an editor)
}

juce::AudioProcessorEditor* FirstVSTAudioProcessor::createEditor()
{
    return new FirstVSTAudioProcessorEditor (*this);
}

//==============================================================================
void FirstVSTAudioProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    // You should use this method to store your parameters in the memory block.
    // You could do that either as raw data, or use the XML or ValueTree classes
    // as intermediaries to make it easy to save and load complex data.
}

void FirstVSTAudioProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    // You should use this method to restore your parameters from this memory block,
    // whose contents will have been created by the getStateInformation() call.
}

//==============================================================================
// This creates new instances of the plugin..
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new FirstVSTAudioProcessor();
}

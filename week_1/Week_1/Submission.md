Week-1 GENAI
Code in Chatbot.py

Key features: I have given a list of 5 models for the user to select on, making the code model agnostic as required. These models can be selected by giving input the serial number.

I have also given the flexiblity for the user to select max turns after which auto compaction will occur, this will be implemented by a check of total number of turns after each model call.

I have used the open router key but since deepseek was giving some issues, I have removed it from the model list.

The default model is a randomly chosen free model from open router

The default number of turns before auto compaction are 4

The api call is put in a try and except block, which in case the api request is failed returns a empty string instead of termination of session.

When max turns are reached, a llm call is made to the same model to summarise all the messages and it is inserted as one message in the conversation history.

Text streaming is set to true, all the models that support it will result in text being displayed as llm predicts tokens.

Overall learning : It was good to play around with openrouter and compaction was great to implement.

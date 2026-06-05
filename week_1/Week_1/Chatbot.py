import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
class ChatAgent:
    def __init__(self,model_name: str,max_turns: int=4):
        self.model_name=model_name
        self.max_turns=max_turns
        self.client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        )

        self.system_prompt = {"role": "system", "content": "You are a helpful assistant."}
        self.messages = [self.system_prompt]

    def Number_of_Turns(self) -> int:
        #remove 1 for system prompt and half the remaining number of messages
        return(len(self.messages)-1)//2
    def compaction(self):
        if len(self.messages)<=3:
              print("\n Not enough history to compact")
              return
        summary="Summarize the following conversation very concisely.Retain context for future calls as well as hold onto any important information as required"
        for i in self.messages[1:]:
             summary+= f"{i['role'].upper()}: {i['content']}\n"
        response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": summary}]
            )
        summary = response.choices[0].message.content
        self.messages=[self.system_prompt,{"role":"system","content":summary}]
        print("Compaction Complete\n")
    def check_turns(self):
         if(len(self.messages)-1)//2 >= self.max_turns:
              self.compaction()
        
    
    def call_model(self) -> str:

     try:
        stream=self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            stream=True
        )

        complete_answer=""
        for i in stream:
            if i.choices[0].delta.content is not None:
                content=i.choices[0].delta.content
                print(content, end="",flush=True)
                complete_answer+=content
        print()
        return complete_answer
     except:
          print("API REQUEST FAILED")
          return " "
    def run(self):
        print("CHAT HAS STARTED")
        print("Model",self.model_name)
        print("type exit to quit and //compact to manually perform compaction\n")
        while True:
            try:
                user_input = input("[YOU] ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n Thank you, goodbye")
                break
            if user_input.lower()=='exit':
                print("Thank you, goodbye")
                break
            elif user_input.lower()=='//compact':
                 self.compaction()
                 continue
            elif not user_input:
                continue

            self.messages.append({"role": "user", "content": user_input})
            answer=self.call_model()
            if answer!=" ":
                 self.messages.append({"role": "assistant", "content": answer})
            self.check_turns()
def main():
            print("Select a model")
            print(" 1. Random free model (Default)\n",
            "2. openrouter/owl-alpha\n",
            "3. Nvidia nemotron 3 super\n",
            "4. Google Gemma 4\n",
            "5. OpenAi Gpt oss\n"
            )
            choice=input("Press 1/2/3/4/5 for respective models or press enter for default")
            models = {
        "1": "openrouter/free",  # The auto-fallback free model router
        "2": "openrouter/owl-alpha",
        "3": "nvidia/nemotron-3-super-120b-a12b:free",
        "4": "google/gemma-4-31b-it:free",
        "5": "openai/gpt-oss-120b:free"
    }
            selected_model=models.get(choice, models["1"])
            turns = input("Enter max turns before compaction ").strip()
            try:
                if not turns:
                      turns=4
                else:
                     turns=int(turns)
                if turns<=3:
                     turns=4
            except:
                 turns=4
                
            agent = ChatAgent(model_name=selected_model, max_turns=turns)
            agent.run()

if __name__ == "__main__":
    main()



        
    
    





        
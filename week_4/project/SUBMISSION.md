**Instructions**
1.Use standard commands to run from week_4/project directory.
```text
pip install openai python-dotenv requests markdownify trafilatura textual
```

This weeks allows the agent to run test and correct code from the target repo. Some of the examples where i tested out the code are:
Python **requests** code: I cloned their repo in target_repo folder and made changes in utills.py file in dotnetmask function specially altering the function formula. Then I asked the agent to find errors in the code by running the test suite. It ran the test suite in which 7 test failed out of 228 initially. Then it saw the error origin and went to utills.py where it used read file tool to see the content. It was able to identify and correct the errors in the code and also verify them before ending the session.

Design decisions: 100 limit on total numbers of loops which can be changed in the code.


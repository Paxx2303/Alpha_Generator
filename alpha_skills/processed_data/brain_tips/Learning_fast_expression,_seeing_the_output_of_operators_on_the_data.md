# Learning fast expression, seeing the output of operators on the data

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/27402122384663-Learning-fast-expression-seeing-the-output-of-operators-on-the-data 
**Metadata:** AW24434 1 year ago

## Post Content

I am learning how to use the fast expression language; I am not new to coding, and I have experience in Python. Usually, I learn how a language works by testing the functions to ensure they produce the intended output. Is there any way to test an algorithm that I am writing by giving it a small amount of data and seeing the output? In the learning videos, there were some example Excel sheets with eight stocks that showed the output of each calculation stage, these were very useful and I would like to be able to break my code down in a similar way. Is there some way to print values out from my code, debug, etc.?

## Comments

### Comment by TT55495 1 year ago
Brain does not give public data points so you will not be able to break down your code as per the method you suggested.

### Comment by PY62071 1 year ago
Fast Expression Languages (FELs) in quantitative finance enable rapid evaluation of mathematical models with low-latency execution. They optimize performance through vectorized computation, domain-specific functions, and memory-efficient processing. FELs integrate seamlessly with trading systems, supporting both real-time and historical data analysis. Examples include Q/KDB+, Zipline, and proprietary hedge fund languages.

---

### Comment by YZ51589 8 months ago
Thanks for raising this — I had the same question when I first started with FEL. The main takeaway for me is that while we can’t “print” values like in Python, there are still good ways to debug. Breaking down expressions into smaller parts and running backtests on limited data windows is really useful. Using small datasets (like the Excel examples) helps you see the operator logic more clearly. Another tip I like is replicating the FEL logic in Python with Pandas to cross-check the outputs — it feels natural if you already have coding experience. Even if it’s not as direct as print debugging, it’s a solid way to build confidence in your signals.

---
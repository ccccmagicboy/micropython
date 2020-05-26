#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os


# In[3]:


os.listdir(os.getcwd())


# In[4]:


i=0
print(i)
for file in os.listdir(os.getcwd()):
    if file.endswith('.py'):
        if 'get_code_lines' in file:
            continue
        if 'template' in file:
            continue
        print(file)
        with open(file, 'r') as ff:
            for line in ff:
                i+=1
        print(i)


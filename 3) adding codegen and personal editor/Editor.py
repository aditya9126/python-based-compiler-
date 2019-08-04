from tkinter import Tk, Frame, Menu, Button
from tkinter import LEFT, TOP, X, FLAT, RAISED,filedialog,Text
from tkinter import *
import os, sys
import Complier as cp

class Example():

    __file=None
    root=Tk("Text Editor")
    root.geometry("250x150+300+300")
    __thisTextArea=Text(root)
    def __openFile(self): 
          
        self.__file = filedialog.askopenfilename(defaultextension=".py", 
                                  filetypes=[("All Files","*.*"), 
                                      ("Text Documents","*.txt"),
                                             ("Python Files","*.py")]) 
  
        if self.__file == "": 
            self.__file = None
        else:
            self.root.title(os.path.basename(self.__file) + " - Notepad") 
            self.__thisTextArea.delete(1.0,END) 
  
            file = open(self.__file,"r") 
  
            self.__thisTextArea.insert(1.0,file.read()) 
  
            file.close() 
  
          
    def __newFile(self): 
        self.root.title("Untitled - Notepad") 
        self.__file = None
        self.__thisTextArea.delete(1.0,END) 
  
    def __saveFile(self): 
  
        if self.__file == None: 
            #save as new file 
            self.__file = filedialog.asksaveasfilename(initialfile='Untitled.py', 
                                            defaultextension=".py", 
                                            filetypes=[("Python Files","*.py")
                                                       ,("All Files","*.*"), 
                                                ("Text Documents","*.txt")]) 
  
            if self.__file == "": 
                self.__file = None
            else: 
              
                # try to save the file 
                file = open(self.__file,"w") 
                file.write(self.__thisTextArea.get(1.0,END)) 
                file.close() 
            # change the window title 
                self.root.title(os.path.basename(self.__file) + " - Notepad") 
                  
              
        else: 
            file = open(self.__file,"w") 
            file.write(self.__thisTextArea.get(1.0,END)) 
            file.close() 
  

    def __init__(self):
        super().__init__()

        self.initUI()

    def compiler(self):
        fname = open(self.__file, 'r')
        text_input = fname.readlines()
        for i in text_input:
            i=i[6:-2]
            try:
                exec(i)
            except ZeroDivisionError:
                print("not complied")
                sys.exit()
                
        lexer = cp.Lexer().get_lexer()

        codegen = cp.CodeGen()
        module = codegen.module
        builder = codegen.builder
        printf = codegen.printf
        for s in text_input:
            
            tokens = lexer.lex(s)

            pg = cp.Parser(module, builder,printf)
            pg.parse() 
            parser = pg.get_parser()    
            parser.parse(tokens)

        codegen.create_ir()
        qwerty = codegen.save_ir()

        with open('{}.ll'.format(self.__file[:-3:]),'w') as output:
            output.write(str(qwerty))
        x='{}'.format(self.__file[:-3:])
        cp.subprocess.call(['llc','-filetype=obj','{}.ll'.format(self.__file[:-3:])])
        cp.subprocess.call(['clang','{}.obj'.format(x),'-o','{}.exe'.format(x)])
        print('Compiled Successfully------------->>')
    def run(self):
        x='{}'.format(self.__file[:-3:])
        w=cp.subprocess.Popen(['{}.exe'.format(x)], stdout= cp.subprocess.PIPE)
        print(w.communicate()[0])
        print('Run Successfully------------->>')
    def initUI(self):

        self.root.title("Text Editor")

        toolbar = Frame(self.root.master, bd=1, relief=RAISED)

        exitButton = Button(toolbar, text='Exit', relief=FLAT,
            command=self.root.destroy)

        newButton = Button(toolbar, text='New', relief=FLAT,
            command=self.__newFile)

        openButton = Button(toolbar, text='Open', relief=FLAT,
            command=self.__openFile)
 
        
        saveButton = Button(toolbar, text='Save', relief=FLAT,
            command=self.__saveFile)

        
        compileButton = Button(toolbar, text='Compile', relief=FLAT,
            command=self.compiler)

        
        runButton = Button(toolbar, text='Run', relief=FLAT,
            command=self.run)
        newButton.pack(side=LEFT, padx=2, pady=2)
        
        openButton.pack(side=LEFT, padx=2, pady=2)
        saveButton.pack(side=LEFT, padx=2, pady=2)
        compileButton.pack(side=LEFT, padx=2, pady=2)
        runButton.pack(side=LEFT, padx=2, pady=2)
        exitButton.pack(side=LEFT, padx=2, pady=2)
        toolbar.pack(side=TOP, fill=X)
        self.__thisTextArea.pack() 

    def onExit(self):
        self.quit()


Example()

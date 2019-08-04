; ModuleID = "xyz"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

define void @"main"() 
{
entry:
  %".2" = add i8 4, 4
  %".3" = bitcast [4 x i8]* @"yovbk" to i8*
  %".4" = call i8 (i8*, ...) @"printf"(i8* %".3", i8 %".2")
  ret void
}

declare i8 @"printf"(i8* %".1", ...) 

@"yovbk" = internal constant [4 x i8] c"\0a%i\00"
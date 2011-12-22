class Greet
   def initialize person
     @@person = person
   end
   def hello
     puts "hello #{@@person}"
   end
end
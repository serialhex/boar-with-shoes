
# this is the boar wrapper class
# it has become a class...  because they're cooler

require 'rubypython'
require 'green_shoes'
require 'pry'

require_relative 'repo'
require_relative 'common'

class BoarWrap
  include Common

  def self.open dir
    self.new dir
  rescue Exception => e
    # i know there is a better way to do this...
    # anybody want to buy me a copy of Exceptional Ruby?? :D
    #alert "we encountered errors :'(\n#{e}"
    return e
  end

  def initialize repo, create = false
    sys 'boar'
    @repo = RepoWrap.new repo, create
    pyfront = RubyPython.import('front')
    @front = pyfront.Front.new(@repo.repo)
  end

  attr_reader :repo

  def method_missing m, *args, &block
    @front.send m, *args, &block
    super
  end
end

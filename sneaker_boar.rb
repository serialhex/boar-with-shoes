#!/usr/bin/env ruby????

require "rubypython"
require 'green_shoes'
require_relative 'lib/help'
require_relative 'lib/boar_wrap'

module MoarKolorz
  def m_purple
    rgb(63,2,70)
  end
  def m_blue
    rgb(4,0,127)
  end
end

Shoes.app title: "Boar with Sneakers", width: 800, height: 600 do
  extend MoarKolorz

  stack width: 0.25, height: 1.0 do
    background m_purple..m_blue

    button("Open Repo"){
      dir = ask_open_folder
      @boar = BoarWrap.open dir
      # yes, i am a cylon....
      unless @boar.kind_of? Exception
        # Exceptional Ruby
        @writing.text = @boar
      else
        if @boar.to_s =~ /CorruptionError/
          # plase?
          if confirm "This dosn't seem to be a repo, make one?"
            dir += '/' + ask("name of this new repo?") if Dir.exist? dir
            @boar = BoarWrap.new dir, true
          end
        else
          raise @boar
        end
      end
    }
    button("blah"){
      # mo stuff
    }
    button("HEEELLLLLLPPPPP!!!!!"){
      # plase?
    }
  end

  stack width: 0.75 , height: 1.0 do
    background m_blue
    @writing = para
  end
end
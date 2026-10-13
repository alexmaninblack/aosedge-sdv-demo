#!/usr/bin/perl
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
# Bounded anonymous Drive response parser. No network, cookies, login or eval.
use strict;
use warnings;

sub stop { die "Unsupported public Drive response; no download accepted.\n"; }
sub decode {
    my ($s)=@_;
    $s =~ s/&amp;/&/g; $s =~ s/&quot;/"/g; $s =~ s/&#39;/'/g;
    $s =~ s/&lt;/</g; $s =~ s/&gt;/>/g;
    return $s;
}
sub encode {
    my ($s)=@_; $s =~ s/([^A-Za-z0-9_.~-])/sprintf('%%%02X',ord($1))/ge;
    return $s;
}
sub url {
    my ($s)=@_; stop() unless length($s)<=4096;
    stop() unless $s =~ m{\Ahttps://(drive\.google\.com/uc|drive\.usercontent\.google\.com/download)\?([^#\s]+)\z};
    my %fields;
    for my $pair (split /&/,$2) {
        stop() unless $pair =~ /\A([a-z]+)=([A-Za-z0-9_.:%-]+)\z/;
        my ($key,$value)=($1,$2); stop() if exists $fields{$key};
        stop() unless $key =~ /\A(?:id|export|resourcekey|confirm|uuid|at)\z/;
        stop() if $value =~ /%(?![A-Fa-f0-9]{2})/;
        $value =~ s/%([A-Fa-f0-9]{2})/chr(hex($1))/ge;
        stop() unless $value =~ /\A[A-Za-z0-9_.:-]{1,2048}\z/;
        $fields{$key}=$value;
    }
    stop() unless ($fields{export}//'') eq 'download' && ($fields{id}//'') =~ /\A[A-Za-z0-9_-]{10,200}\z/;
    return %fields;
}
sub attrs {
    my ($text)=@_; my %result;
    while ($text =~ /([A-Za-z][A-Za-z0-9_-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')/g) {
        my ($key,$value)=(lc($1),defined($2)?$2:$3); stop() if exists $result{$key};
        $result{$key}=decode($value);
    }
    return %result;
}
my ($mode,$path,$original)=@ARGV; stop() unless @ARGV==3;
my %expected=url($original);
stop() unless -f $path && !-l $path && (-s $path)<=65536;
open my $file,'<',$path or stop(); local $/; my $raw=<$file>;close $file;
if ($mode eq 'headers') {
    my @blocks=grep {/\AHTTP\//} split /\r?\n\r?\n/,$raw;
    stop() unless @blocks;my $head=$blocks[-1];
    stop() unless $head =~ /\AHTTP\/[0-9.]+ ([0-9]{3})\b/;my $status=$1;
    if ($status =~ /\A30[12378]\z/) {
        my @locations=($head =~ /^location:[ \t]*([^\r\n]+)\r?$/mig);stop() unless @locations==1;
        my $location=$locations[0];my %fields=url($location);
        stop() unless $fields{id} eq $expected{id} &&
          (!exists($expected{resourcekey}) || ($fields{resourcekey}//'') eq $expected{resourcekey});
        print "redirect\t$location\n";
    } else {
        stop() unless $status==200;
        my @types=($head =~ /^content-type:\s*([^\r\n;]+)/mig);stop() unless @types==1;
        if (lc($types[0]) eq 'text/html') {print "html\t$original\n";}
        elsif (lc($types[0]) =~ /\Aapplication\/(?:octet-stream|x-apple-diskimage|binary)\z/) {print "binary\t$original\n";}
        else {stop();}
    }
} elsif ($mode eq 'form') {
    my $text=lc(decode($raw));
    $text =~ s/<script\b.*?<\/script\s*>//sg;
    $text =~ s/<style\b.*?<\/style\s*>//sg;
    $text =~ s/<[^>]*>/ /sg; $text =~ s/\s+/ /g;
    stop() unless $text =~ /(?:can't scan this file for viruses|too large for google to scan for viruses)/ &&
      $text !~ /too many users|download quota|malware|abusive|violates|infected/;
    my @forms;
    while ($raw =~ /<form\b([^>]*)>(.*?)<\/form\s*>/sig) {
        my ($attrs,$body)=($1,$2);my %a=attrs($attrs);
        push @forms,[\%a,$body] if ($a{id}//'') eq 'download-form';
    }
    stop() unless @forms==1;my ($a,$body)=@{$forms[0]};
    stop() unless ($a->{action}//'') eq 'https://drive.usercontent.google.com/download' &&
                  lc($a->{method}//'get') eq 'get';
    my %fields;
    while ($body =~ /<input\b([^>]*)>/sig) {
        my %a=attrs($1);
        # The unnamed submit control is presentation, not a query parameter.
        # Never execute its attributes or accept a named/unknown input instead.
        next if ($a{type}//'') eq 'submit' && !exists($a{name});
        stop() unless ($a{type}//'') eq 'hidden';
        my ($key,$value)=($a{name},$a{value});
        stop() unless defined($key) && defined($value) && !exists($fields{$key}) &&
          $key =~ /\A(?:id|export|resourcekey|confirm|uuid|at)\z/ &&
          $value =~ /\A[A-Za-z0-9_.:-]{1,2048}\z/;
        $fields{$key}=$value;
    }
    stop() unless ($fields{id}//'') eq $expected{id} && ($fields{export}//'') eq 'download' &&
                  ($fields{confirm}//'') eq 't';
    if (exists $expected{resourcekey}) {
        stop() if exists($fields{resourcekey}) && $fields{resourcekey} ne $expected{resourcekey};
        $fields{resourcekey}=$expected{resourcekey};
    }
    my $result=$a->{action}.'?'.join('&',map {encode($_).'='.encode($fields{$_})} sort keys %fields);
    url($result);print "confirm\t$result\n";
} else {stop();}

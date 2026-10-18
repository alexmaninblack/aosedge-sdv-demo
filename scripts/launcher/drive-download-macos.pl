#!/usr/bin/perl
# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
# Bounded anonymous Drive/Dropbox parser. No network, cookies, login or eval.
use strict;
use warnings;

sub stop { die "Unsupported public artifact response; no download accepted.\n"; }
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
    if ($s =~ m{\Ahttps://www\.dropbox\.com/scl/(?:fi/[A-Za-z0-9_-]{8,200}|fo/[A-Za-z0-9_-]{8,200}/[A-Za-z0-9_-]{8,200})/([A-Za-z0-9_.%~-]{1,255}\.dmg)\?([^#\s]+)\z}) {
        my ($name,$query)=($1,$2); stop() if $name =~ /%(?![A-Fa-f0-9]{2})/;
        $name =~ s/%([A-Fa-f0-9]{2})/chr(hex($1))/ge;
        stop() if $name =~ m{[/\\\x00-\x1f\x7f]} || $name =~ /\A\.\.?\z/;
        my %fields;
        for my $pair (split /&/,$query) {
            stop() unless $pair =~ /\A(rlkey|st|dl)=([A-Za-z0-9_-]{1,200})\z/;
            stop() if exists $fields{$1}; $fields{$1}=$2;
        }
        stop() unless ($fields{dl}//'') eq '1' && ($fields{rlkey}//'') =~ /\A[A-Za-z0-9_-]{8,200}\z/;
        return (provider=>'dropbox');
    }
    if ($s =~ m{\Ahttps://(?:[a-z0-9-]{1,100}\.)?dl\.dropboxusercontent\.com/cd/0/(?:inline|inline2|get|get2|attachment)/[A-Za-z0-9_-]{10,2048}/file\?dl=1\z}) {
        return (provider=>'dropbox');
    }
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
my ($mode,$path,$original,$approved_size,$offset)=@ARGV;
my $transfer=$mode eq 'transfer-headers';
stop() unless $transfer ? @ARGV==5 : (@ARGV==3 || @ARGV==4);
stop() if defined($approved_size) && $approved_size !~ /\A[1-9][0-9]{0,18}\z/;
stop() if $transfer && (!defined($approved_size) || $offset !~ /\A(?:0|[1-9][0-9]{0,18})\z/ || $offset >= $approved_size);
my %expected=url($original);
stop() unless -f $path && !-l $path && (-s $path)<=65536;
open my $file,'<',$path or stop(); local $/; my $raw=<$file>;close $file;
if ($mode eq 'payload-status') {
    my $text=lc(decode($raw));
    $text =~ s/<[^>]*>/ /sg; $text =~ s/\s+/ /g;
    print $text =~ /quota exceeded|too many users.*downloaded|can't view or download this file/ ? "quota\n" : "unsupported\n";
} elsif ($mode eq 'headers' || $transfer) {
    my @blocks=grep {/\AHTTP\//} split /\r?\n\r?\n/,$raw;
    stop() unless @blocks;my $head=$blocks[-1];
    stop() unless $head =~ /\AHTTP\/[0-9.]+ ([0-9]{3})\b/;my $status=$1;
    if ($transfer) {
        stop() unless $status==($offset ? 206 : 200);
        my @ranges=($head =~ /^content-range:[ \t]*([^\r\n]+)\r?$/mig);
        if ($offset) {
            stop() unless @ranges==1 && $ranges[0] eq 'bytes '.$offset.'-'.($approved_size-1).'/'.$approved_size;
        } else { stop() if @ranges; }
        my @lengths=($head =~ /^content-length:[ \t]*([^\r\n]+)\r?$/mig);
        stop() unless @lengths<=1 && (!@lengths || $lengths[0] eq ''.($approved_size-$offset));
        my @encodings=($head =~ /^content-encoding:[ \t]*([^\r\n]+)\r?$/mig);
        stop() unless @encodings<=1 && (!@encodings || lc($encodings[0]) eq 'identity');
    }
    if ($status =~ /\A30[12378]\z/) {
        my @locations=($head =~ /^location:[ \t]*([^\r\n]+)\r?$/mig);stop() unless @locations==1;
        my $location=$locations[0];
        # Dropbox's CDN redirect ends with an empty fragment; never accept a
        # meaningful fragment or another provider as an automatic fallback.
        $location =~ s/#\z// if ($expected{provider}//'') eq 'dropbox';
        if (($expected{provider}//'') eq 'dropbox' && $location =~ m{\A/(?!/)}) {
            stop() unless $original =~ m{\A(https://(?:[a-z0-9-]{1,100}\.)?dl\.dropboxusercontent\.com)/};
            $location=$1.$location;
        }
        my %fields=url($location);
        if (($expected{provider}//'') eq 'dropbox') {
            stop() unless ($fields{provider}//'') eq 'dropbox';
        } else {
            stop() if exists $fields{provider};
            stop() unless $fields{id} eq $expected{id} &&
              (!exists($expected{resourcekey}) || ($fields{resourcekey}//'') eq $expected{resourcekey});
        }
        print "redirect\t$location\n";
    } else {
        stop() unless $status==200 || ($transfer && $status==206);
        my @types=($head =~ /^content-type:\s*([^\r\n;]+)/mig);stop() unless @types==1;
        if (lc($types[0]) eq 'text/html') {stop() if $transfer;print "html\t$original\n";}
        elsif (lc($types[0]) =~ /\Aapplication\/(?:octet-stream|x-apple-diskimage|binary)\z/) {print "binary\t$original\n";}
        elsif (($expected{provider}//'') eq 'dropbox' && lc($types[0]) eq 'application/json') {
            # Folder-member links currently label the DMG as JSON/unspecified.
            # Accept only this observed CDN attachment with the independently
            # approved full byte count. SHA-256 and signature checks still run
            # before mounting or executing; this is not a content attestation.
            stop() unless $original =~ m{\Ahttps://(?:[a-z0-9-]{1,100}\.)?dl\.dropboxusercontent\.com/};
            my @sizes=($head =~ /^content-length:[ \t]*([0-9]+)\r?$/mig);
            my @dispositions=($head =~ /^content-disposition:[ \t]*([^\r\n]+)\r?$/mig);
            my $length=defined($approved_size) ? $approved_size-($transfer ? $offset : 0) : undef;
            stop() unless defined($length) && @sizes==1 && $sizes[0] eq $length &&
              @dispositions==1 && $dispositions[0] =~ /\Aattachment;[ \t]*filename=(?:unspecified|"unspecified")\z/i;
            print "binary\t$original\n";
        }
        else {stop();}
    }
} elsif ($mode eq 'form') {
    stop() if exists $expected{provider};
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

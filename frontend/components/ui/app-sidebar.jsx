"use client";
import React from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  Calendar,
  ChevronUp,
  Home,
  Inbox,
  Settings,
  Timer,
  User2,
  LogOut,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import Cookies from "js-cookie";
import { jwtDecode } from "jwt-decode";

const AppSidebar = () => {
  const router = useRouter();
  const pathname = usePathname();

  const getUserInfo = () => {
    console.log(Cookies.get("access_token"));
    const token = Cookies.get("access_token");

    try {
      const decoded = jwtDecode(token);
      return {
        email: decoded.sub,
        role: decoded.role,
      };
    } catch (error) {
      console.log(error);
      router.push("/login");
    }
  };
  const { email, role } = getUserInfo();
  const rolePrefix =
    role === "mahasiswa"
      ? "/mahasiswa"
      : role === "dosen"
      ? "/dosen"
      : role === "admin"
      ? "/admin"
      : "/guest";

  // Define sidebar items for each role
  let sidebarItems = [];

  if (role === "mahasiswa") {
    sidebarItems = [
      { title: "Dashboard", url: `${rolePrefix}/dashboard`, icon: Home },
      { title: "Schedule", url: `${rolePrefix}/schedule`, icon: Calendar },
      { title: "Profile", url: `${rolePrefix}/profile`, icon: User2 },
    ];
  } else if (role === "dosen") {
    sidebarItems = [
      { title: "Dashboard", url: `${rolePrefix}/dashboard`, icon: Home },
      { title: "Schedule", url: `${rolePrefix}/jadwal`, icon: Calendar },
      { title: "Preferences", url: `${rolePrefix}/preferensi`, icon: Settings },
      { title: "Profile", url: `${rolePrefix}/profile`, icon: User2 },
    ];
  } else if (role === "admin") {
    sidebarItems = [
      { title: "Dashboard", url: `${rolePrefix}/dashboard`, icon: Home },
      {
        title: "Data Management",
        url: `${rolePrefix}/data-manajemen`,
        icon: Inbox,
      },
      { title: "Schedule", url: `${rolePrefix}/jadwal`, icon: Calendar },
      {
        title: "Dosen Preferences",
        url: `${rolePrefix}/preferensi-dosen`,
        icon: Settings,
      },
    ];
  }
  return (
    <Sidebar className="bg-sidebar text-sidebar-foreground min-h-screen w-64 border-r border-sidebar-border">
      <SidebarHeader className="p-4">
        <Link href="/">
          <h1 className="text-2xl font-bold text-primary flex gap-x-2 items-center">
            <Timer />
            <span>GenPlan</span>
          </h1>
        </Link>
        <hr className="border-sidebar-border mt-2" />
      </SidebarHeader>

      <SidebarContent className="">
        <SidebarGroup>
          <SidebarGroupLabel className="text-text-secondary text-sm mb-2">
            Navigation
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {sidebarItems.map((item) => (
                <SidebarMenuItem key={item.title} url={item.url}>
                  <SidebarMenuButton
                    asChild
                    className={`flex items-center gap-x-3 px-4 py-2 rounded-lg ${
                      pathname.startsWith(item.url)
                        ? "bg-primary text-primary-foreground font-medium"
                        : "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition"
                    }`}
                  >
                    <a href={item.url} className="flex items-center gap-x-3">
                      <item.icon className="size-5" />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Sidebar Footer */}
      <SidebarFooter className="mt-auto p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton className="py-3 text-sm flex items-center gap-x-3 w-full">
                  <Avatar className="size-8">
                    <AvatarImage src="https://github.com/shadcn.png" />
                    <AvatarFallback>CN</AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col text-text-secondary">
                    <p className="text-text-primary font-semibold">{email}</p>
                    <p className="text-xs">{role}</p>
                  </div>
                  <ChevronUp className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="top"
                className="w-[--radix-popper-anchor-width]"
              >
                <DropdownMenuItem>
                  <span>Account</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <span>Billing</span>
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="text-error font-medium"
                  onClick={() => Cookies.remove("access_token")}
                >
                  <LogOut className="size-4 mr-2" />
                  <Link href="/">Sign out</Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
};

export default AppSidebar;
